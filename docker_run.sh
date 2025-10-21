#!/usr/bin/env bash
set -e

APP_NAME="multiwall"
IMAGE_NAME="multiwall:latest"

# Colores bonitos :)
GREEN="\e[32m"
CYAN="\e[36m"
RESET="\e[0m"

echo -e "${CYAN}=== Multiwall GTK4 Docker Launcher ===${RESET}"

# Verificar flag --build
FORCE_BUILD=false
if [[ "$1" == "--rebuild" ]]; then
  FORCE_BUILD=true
  shift
fi

# 1️⃣ Detectar si hay Docker
if ! command -v docker &> /dev/null; then
  echo "❌ Docker no está instalado. Instálalo primero."
  exit 1
fi

# 2️⃣ Asegurar que el directorio de configuración existe con permisos correctos
echo -e "${GREEN}→ Preparando directorios...${RESET}"
mkdir -p "$HOME/.config/multiwall"
chmod 755 "$HOME/.config/multiwall"

# Detectar el directorio de imágenes del sistema
PICTURES_DIR="$HOME/Images"
if command -v xdg-user-dir &> /dev/null; then
  XDG_PICTURES=$(xdg-user-dir PICTURES 2>/dev/null)
  if [[ -n "$XDG_PICTURES" ]] && [[ -d "$XDG_PICTURES" ]]; then
    PICTURES_DIR="$XDG_PICTURES"
    echo -e "${GREEN}✔ Directorio de imágenes detectado: $PICTURES_DIR${RESET}"
  fi
else
  echo -e "${GREEN}✔ Usando directorio por defecto: $PICTURES_DIR${RESET}"
fi

# 3️⃣ Construir imagen si no existe o si se solicita
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo -e "${GREEN}→ Construyendo imagen $IMAGE_NAME...${RESET}"
  docker build -t $IMAGE_NAME .
else
  echo -e "${GREEN}✔ Imagen existente detectada.${RESET}"
  if [[ "$FORCE_BUILD" == true ]]; then
    echo -e "${GREEN}→ Reconstruyendo imagen $IMAGE_NAME...${RESET}"
    docker build -t $IMAGE_NAME .
  fi
fi

# 4️⃣ Detectar entorno gráfico (X11 o Wayland)
if [[ -n "$WAYLAND_DISPLAY" ]]; then
  DISPLAY_MODE="wayland"
elif [[ -n "$DISPLAY" ]]; then
  DISPLAY_MODE="x11"
else
  echo "⚠️ No se detectó entorno gráfico (ni X11 ni Wayland)."
  echo "Ejecuta desde una sesión gráfica."
  exit 1
fi

# 5️⃣ Configurar flags de entorno gráfico
USER_ID=$(id -u)
RUNTIME_DIR="/run/user/$USER_ID"

DOCKER_FLAGS=(
  -it --rm
  -e LANG=es_CO.UTF-8
  -e LC_ALL=es_CO.UTF-8
  -e LANGUAGE=es_CO:es
  -e PYTHONIOENCODING=utf-8  
  -e DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$USER_ID/bus"
  -e XDG_RUNTIME_DIR=/run/user/$USER_ID
  -e GSETTINGS_BACKEND=dconf
  -v "$RUNTIME_DIR/bus:/run/user/$USER_ID/bus"
  -v "$PWD:/app"
  -e HOME=$HOME
  -v "$HOME/.config/dconf:$HOME/.config/dconf:rw"
  -v "$PICTURES_DIR:$PICTURES_DIR:ro"
  -v "$HOME/.config/multiwall:$HOME/.config/multiwall:rw"
  -v "$HOME/.config/user-dirs.dirs:$HOME/.config/user-dirs.dirs:ro"
  -w /app
  --device /dev/dri
  --user $USER_ID:$(id -g)
)

if [[ "$DISPLAY_MODE" == "x11" ]]; then
  echo -e "${GREEN}→ Usando modo gráfico X11${RESET}"
  xhost +local:docker > /dev/null 2>&1 || true
  DOCKER_FLAGS+=(
    -e DISPLAY=$DISPLAY
    -v /tmp/.X11-unix:/tmp/.X11-unix
  )
elif [[ "$DISPLAY_MODE" == "wayland" ]]; then
  echo -e "${GREEN}→ Usando modo gráfico Wayland${RESET}"
  
  DOCKER_FLAGS+=(
    -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY    
    -v "$RUNTIME_DIR/$WAYLAND_DISPLAY:/run/user/$USER_ID/$WAYLAND_DISPLAY"
    -e GDK_BACKEND=wayland
  )
fi

# 6️⃣ Ejecutar contenedor
echo -e "${CYAN}→ Ejecutando aplicación dentro del contenedor...${RESET}"
docker run "${DOCKER_FLAGS[@]}" "$IMAGE_NAME" /app/.venv/bin/python main.py