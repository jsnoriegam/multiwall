#!/bin/bash
set -e

echo "🔨 Construyendo MultiWall AppImage..."

APP_NAME="MultiWall"
APP_DIR="/build/${APP_NAME}.AppDir"
VERSION="${VERSION:-0.1.0}"

# Crear estructura AppDir
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/lib"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/usr/share/multiwall"

# Crear entorno virtual de Python
echo "📦 Creando entorno virtual..."
python3 -m venv "$APP_DIR/usr/venv"
source "$APP_DIR/usr/venv/bin/activate"

# Instalar dependencias
pip install --upgrade pip
pip install PyGObject Pillow pyyaml python-i18n

# Copiar aplicación
echo "📋 Copiando aplicación..."
cp -r /app/multiwall "$APP_DIR/usr/share/multiwall/"
cp /app/main.py "$APP_DIR/usr/share/multiwall/"
cp /app/requirements.txt "$APP_DIR/usr/share/multiwall/"

# Crear script de lanzamiento
cat > "$APP_DIR/usr/bin/multiwall" << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
export PYTHONPATH="$APPDIR/usr/share/multiwall:$PYTHONPATH"
source "$APPDIR/usr/venv/bin/activate"
cd "$APPDIR/usr/share/multiwall"
exec python3 main.py "$@"
EOF
chmod +x "$APP_DIR/usr/bin/multiwall"

# Crear AppRun
cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="$APPDIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="$APPDIR/usr/share/multiwall:$PYTHONPATH"
export XDG_DATA_DIRS="$APPDIR/usr/share:$XDG_DATA_DIRS"

# Activar entorno virtual
source "$APPDIR/usr/venv/bin/activate"

# Ejecutar aplicación
cd "$APPDIR/usr/share/multiwall"
exec python3 main.py "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# Crear archivo .desktop
cat > "$APP_DIR/usr/share/applications/multiwall.desktop" << EOF
[Desktop Entry]
Name=MultiWall
Comment=Multi-Monitor Wallpaper Manager
Exec=multiwall
Icon=multiwall
Type=Application
Categories=Utility;Graphics;GTK;
Terminal=false
EOF

# Copiar .desktop también a la raíz del AppDir (requisito de appimagetool)
cp "$APP_DIR/usr/share/applications/multiwall.desktop" "$APP_DIR/multiwall.desktop"

# Copiar icono (usar el existente en la raíz)
if [ -f "/app/icon.png" ]; then
    echo "📸 Usando icono existente..."
    cp /app/appimage/icon.png "$APP_DIR/usr/share/icons/hicolor/256x256/apps/multiwall.png"
    cp /app/appimage/icon.png "$APP_DIR/multiwall.png"    # <-- copiar icon a la raíz del AppDir
else
    echo "⚠️ Advertencia: No se encontró icon.png, creando icono por defecto..."
    # Crear icono simple SVG como fallback
    cat > "$APP_DIR/usr/share/icons/hicolor/256x256/apps/multiwall.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#3584e4"/>
  <text x="128" y="140" font-size="120" text-anchor="middle" fill="white">🖼️</text>
</svg>
EOF
    # copiar fallback SVG al root del AppDir (appimagetool detecta svg también)
    cp "$APP_DIR/usr/share/icons/hicolor/256x256/apps/multiwall.svg" "$APP_DIR/multiwall.svg"
fi

# Generar AppImage
echo "🎁 Generando AppImage..."
cd /build

# Usar appimagetool extraído
ARCH=x86_64 /usr/local/bin/appimagetool.AppDir/AppRun "$APP_DIR" "/output/MultiWall-${VERSION}-x86_64.AppImage"

echo "✅ AppImage creado: /output/MultiWall-${VERSION}-x86_64.AppImage"
ls -lh /output/*.AppImage