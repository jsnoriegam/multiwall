#!/bin/bash
set -e

echo "📸 Configurando icono para Flatpak..."

# Verificar que existe icon.png
if [ ! -f "multiwall_icon.png" ]; then
    echo "❌ Error: No se encontró icon.png en la raíz del proyecto"
    exit 1
fi

# Buscar ImageMagick: magick (v7+) o convert (v6)
if command -v magick >/dev/null 2>&1; then
  IMAGEMAGICK_BIN="magick"
elif command -v convert >/dev/null 2>&1; then
  IMAGEMAGICK_BIN="convert"
else
  echo "Error: ImageMagick no encontrado (magick o convert). Instala 'imagemagick' en el runner." >&2
  exit 1
fi

echo "Using ImageMagick binary: ${IMAGEMAGICK_BIN}"

# Ejemplo de uso: generar icono 256x256 a partir de icon.svg o icon.png
SRC_ICON="./multiwall_icon.png"
if [ ! -f "${SRC_ICON}" ]; then
  echo "No se encontró ${SRC_ICON}, creando icono placeholder..."
  # crear un png simple si no existe
  "${IMAGEMAGICK_BIN}" -size 256x256 canvas:"#3584e4" -gravity center -pointsize 120 -annotate 0 "🖼️" /tmp/multiwall_icon.png
  SRC_ICON="/tmp/multiwall_icon.png"
fi

# Crear directorio appimage si no existe
mkdir -p appimage

# Copiar icono con el nombre correcto para Flatpak
"${IMAGEMAGICK_BIN}" "${SRC_ICON}" -resize 256x256 "appimage/icon.png"
cp appimage/icon.png multiwall/

# Crear directorio flatpak si no existe
mkdir -p flatpak

# Copiar icono con el nombre correcto para Flatpak
"${IMAGEMAGICK_BIN}" "${SRC_ICON}" -resize 512x512 "flatpak/com.latinosoft.MultiWall.png"

echo "✅ Icono copiado a flatpak/com.latinosoft.MultiWall.png"

# Generar diferentes tamaños si tienes ImageMagick
echo "🎨 Generando diferentes tamaños de icono..."
    
mkdir -p flatpak/icons

for size in 16 32 48 64 128 256 512; do
    "${IMAGEMAGICK_BIN}" "${SRC_ICON}" -resize ${size}x${size} "flatpak/icons/com.latinosoft.MultiWall-${size}.png"
    echo "  ✓ ${size}x${size}"
done

echo "✅ Iconos generados en flatpak/icons/"