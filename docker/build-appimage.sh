#!/bin/bash
set -e

echo "🔨 Construyendo MultiWall AppImage..."

APP_NAME="MultiWall"
APP_DIR="/build/${APP_NAME}.AppDir"
VERSION="${VERSION:-0.1.0}"

# Limpiar AppDir
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin" "$APP_DIR/usr/lib" "$APP_DIR/usr/share/multiwall"

echo "📦 Copiando aplicación..."
# Copia tu aplicación Python al AppDir
cp -r /app/multiwall "$APP_DIR/usr/share/multiwall/"
cp -r /app/fonts "$APP_DIR/usr/share/multiwall/"
cp /app/main.py "$APP_DIR/usr/share/multiwall/"
cp /app/requirements.txt "$APP_DIR/usr/share/multiwall/"

echo "🐍 Configurando entorno Python..."
# Crear entorno virtual local (fuera de AppDir)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias dentro del venv
pip install --upgrade pip
pip install -r /app/requirements.txt

# Copiar solo el venv al AppDir
cp -r venv "$APP_DIR/usr/"

PYTHON_VERSION=$(ls -d /usr/lib/python*.* | head -n 1 | xargs basename | sed 's/python//')

# Copiar binarios del Python base al AppDir
cp "$(which python3)" "$APP_DIR/usr/bin/"
cp -r "/usr/lib/python$PYTHON_VERSION" "$APP_DIR/usr/lib/" || echo "⚠️ Saltando copia de stdlib (verifica ruta del Python base)"

echo "⚙️ Creando AppRun..."
cat > "$APP_DIR/AppRun" << EOF
#!/bin/bash
APPDIR="\$(dirname "\$(readlink -f "\$0")")"

# Configurar entorno
export PATH="\$APPDIR/usr/bin:\$PATH"
export LD_LIBRARY_PATH="\$APPDIR/usr/lib:\$LD_LIBRARY_PATH"
export PYTHONHOME="\$APPDIR/usr"
export PYTHONPATH="\$APPDIR/usr/share/multiwall:\$APPDIR/usr/venv/lib/python$PYTHON_VERSION/site-packages:\$PYTHONPATH"
export XDG_DATA_DIRS="\$APPDIR/usr/share:\$XDG_DATA_DIRS"

# Ejecutar aplicación
cd "\$APPDIR/usr/share/multiwall"
exec "\$APPDIR/usr/bin/python3" main.py "\$@"
EOF
chmod +x "$APP_DIR/AppRun"

echo "🧱 Creando archivo .desktop..."
cat > "$APP_DIR/$APP.desktop" << EOF
[Desktop Entry]
Type=Application
Name=MultiWall
Exec=AppRun
Icon=multiwall
Categories=Utility;Graphics;GTK;
EOF

echo "🖼️ Copiando ícono..."
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
cp /app/appimage/icon.png "$APP_DIR/usr/share/icons/hicolor/256x256/apps/multiwall.png"
cp /app/appimage/icon.png "$APP_DIR/multiwall.png"

# Generar AppImage
echo "🎁 Generando AppImage..."
cd /build

# Usar appimagetool extraído
ARCH=x86_64 /usr/local/bin/appimagetool.AppDir/AppRun "$APP_DIR" "/output/MultiWall-${VERSION}-x86_64.AppImage"

echo "✅ AppImage creado: /output/MultiWall-${VERSION}-x86_64.AppImage"
ls -lh /output/*.AppImage