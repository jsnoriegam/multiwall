#!/bin/bash
set -e

echo "📸 Configurando icono para Flatpak..."

# Verificar que existe icon.png
if [ ! -f "icon.png" ]; then
    echo "❌ Error: No se encontró icon.png en la raíz del proyecto"
    exit 1
fi

# Crear directorio appimage si no existe
mkdir -p appimage

# Copiar icono con el nombre correcto para Flatpak
magick icon.png -resize 256x256 "appimage/icon.png"

# Crear directorio flatpak si no existe
mkdir -p flatpak

# Copiar icono con el nombre correcto para Flatpak
magick icon.png -resize 512x512 "flatpak/com.latinosoft.MultiWall.png"

echo "✅ Icono copiado a flatpak/com.latinosoft.MultiWall.png"

# Opcional: generar diferentes tamaños si tienes ImageMagick
if command -v convert &> /dev/null; then
    echo "🎨 Generando diferentes tamaños de icono..."
    
    mkdir -p flatpak/icons
    
    for size in 16 32 48 64 128 256 512; do
        magick icon.png -resize ${size}x${size} "flatpak/icons/com.latinosoft.MultiWall-${size}.png"
        echo "  ✓ ${size}x${size}"
    done
    
    echo "✅ Iconos generados en flatpak/icons/"
else
    echo "⚠️ ImageMagick no instalado, solo se usará el icono principal"
fi