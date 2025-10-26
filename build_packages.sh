#!/usr/bin/env bash
set -e

GREEN="\e[32m"
CYAN="\e[36m"
YELLOW="\e[33m"
RESET="\e[0m"

VERSION="${VERSION:-0.1.0}"
OUTPUT_DIR="$(pwd)/dist"

echo -e "${CYAN}=== MultiWall Package Builder ===${RESET}"
echo -e "${YELLOW}Version: ${VERSION}${RESET}"

# --- NUEVO: Procesamiento del argumento 'rebuild' ---
FORCE_REBUILD=false
if [[ "$1" == "rebuild" ]]; then
    FORCE_REBUILD=true
    shift # Elimina 'rebuild' de la lista de argumentos
    echo -e "${YELLOW}⚡ Reconstrucción forzada de imágenes de Docker HABILITADA${RESET}"
fi
# --------------------------------------------------

# Verificar que existe el icono
if [ ! -f "multiwall_icon.png" ]; then
    echo -e "${YELLOW}⚠️ Advertencia: No se encontró icon.png en la raíz${RESET}"
    echo "Se usará un icono por defecto"
fi

# Crear directorio de salida
mkdir -p "$OUTPUT_DIR"

# --- MODIFICADO: Función de uso actualizada ---
usage() {
    echo "Uso: $0 [rebuild] [appimage|flatpak|all]"
    echo ""
    echo "Argumentos:"
    echo "  rebuild   - Forzar la reconstrucción de las imágenes de Docker antes de construir"
    echo "  appimage  - Generar AppImage"
    echo "  flatpak   - Generar Flatpak"
    echo "  all       - Generar ambos (por defecto)"
    exit 1
}

# --- MODIFICADO: Función para construir AppImage ---
build_appimage() {
    echo -e "${GREEN}→ Construyendo AppImage...${RESET}"
    
    # Construir imagen de Docker si no existe O si se fuerza
    if [[ "$FORCE_REBUILD" == "true" ]] || [[ "$(docker images -q multiwall-appimage-local 2> /dev/null)" == "" ]]; then
        if [[ "$FORCE_REBUILD" == "true" ]]; then
            echo "Construyendo imagen de Docker para AppImage (forzado)..."
        else
            echo "Construyendo imagen de Docker para AppImage..."
        fi
        docker build \
        --build-arg USER_ID=$(id -u) \
        --build-arg GROUP_ID=$(id -g) \
        -f docker/Dockerfile.appimage -t multiwall-appimage-local docker/
    fi
    
    # Ejecutar construcción
    docker run --rm \
        -v "$(pwd):/app" \
        -v "$OUTPUT_DIR:/output" \
        -e VERSION="$VERSION" \
        multiwall-appimage-local
    
    echo -e "${GREEN}✅ AppImage generado en: ${OUTPUT_DIR}/MultiWall-${VERSION}-x86_64.AppImage${RESET}"
}

# --- MODIFICADO: Función para construir Flatpak ---
build_flatpak() {
    echo -e "${GREEN}→ Construyendo Flatpak...${RESET}"
    
    # Verificar que existe el directorio flatpak
    if [ ! -d "flatpak" ]; then
        echo -e "${YELLOW}Creando estructura de flatpak...${RESET}"
        mkdir -p flatpak
    fi
    
    # Construir imagen de Docker si no existe O si se fuerza
    if [[ "$FORCE_REBUILD" == "true" ]] || [[ "$(docker images -q multiwall-flatpak 2> /dev/null)" == "" ]]; then
        if [[ "$FORCE_REBUILD" == "true" ]]; then
            echo "Construyendo imagen de Docker para Flatpak (forzado)..."
        else
            echo "Construyendo imagen de Docker para Flatpak..."
        fi
        docker build \
        --build-arg USER_ID=$(id -u) \
        --build-arg GROUP_ID=$(id -g) \
        -f docker/Dockerfile.flatpak -t multiwall-flatpak docker/
    fi
    
    # Ejecutar construcción con acceso a red
    docker run --rm \
        --privileged \
        -v "$(pwd):/app:ro" \
        -v "$OUTPUT_DIR:/output" \
        -e VERSION="$VERSION" \
        --network=host \
        multiwall-flatpak
    
    echo -e "${GREEN}✅ Flatpak generado en: ${OUTPUT_DIR}/MultiWall-${VERSION}-x86_64.flatpak${RESET}"
}

# --- MODIFICADO: Procesar argumentos (ahora usa $1 después del shift) ---
TARGET="${1:-all}"

case "$TARGET" in
    appimage)
        build_appimage
        ;;
    flatpak)
        build_flatpak
        ;;
    all)
        build_appimage
        build_flatpak
        ;;
    *)
        usage
        ;;
esac

echo ""
echo -e "${CYAN}=== Construcción completada ===${RESET}"
echo -e "Paquetes generados en: ${GREEN}${OUTPUT_DIR}${RESET}"
ls -lh "$OUTPUT_DIR"

echo ""
echo -e "${YELLOW}Para instalar:${RESET}"
if [ -f "$OUTPUT_DIR/MultiWall-${VERSION}-x86_64.AppImage" ]; then
    echo -e "  AppImage: ${GREEN}chmod +x $OUTPUT_DIR/MultiWall-${VERSION}-x86_64.AppImage && $OUTPUT_DIR/MultiWall-${VERSION}-x86_64.AppImage${RESET}"
fi
if [ -f "$OUTPUT_DIR/MultiWall-${VERSION}-x86_64.flatpak" ]; then
    echo -e "  Flatpak:  ${GREEN}flatpak install --user $OUTPUT_DIR/MultiWall-${VERSION}-x86_64.flatpak${RESET}"
fi