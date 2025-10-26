#!/bin/bash
set -e

echo "🔨 Construyendo MultiWall AppImage..."

echo "El usuario actual es: ${USER}" $(whoami)

APP_NAME="MultiWall"
APP_DIR="/build/${APP_NAME}.AppDir"
VERSION="${VERSION:-0.1.0}"

# Limpiar AppDir
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin" "$APP_DIR/usr/lib" "$APP_DIR/usr/share/multiwall"

echo "📦 Copiando aplicación..."
cp -r /app/multiwall "$APP_DIR/usr/share/multiwall/"
cp -r /app/fonts "$APP_DIR/usr/share/multiwall/"
cp /app/main.py "$APP_DIR/usr/share/multiwall/"
cp /app/requirements.txt "$APP_DIR/usr/share/multiwall/"

echo "🐍 Configurando entorno Python..."
# Crear entorno virtual local
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r /app/requirements.txt

# Copiar venv al AppDir
cp -r venv "$APP_DIR/usr/"

# Detectar versión de Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📌 Usando Python $PYTHON_VERSION"

# Copiar binario de Python
cp "$(which python3)" "$APP_DIR/usr/bin/"

# ========================================
# COPIAR SOLO LIBRERÍAS ESENCIALES
# ========================================
echo "📚 Copiando librerías esenciales de Python..."

PYTHON_STDLIB="/usr/lib/python${PYTHON_VERSION}"
TARGET_STDLIB="$APP_DIR/usr/lib/python${PYTHON_VERSION}"

if [ -d "$PYTHON_STDLIB" ]; then
    mkdir -p "$TARGET_STDLIB"
    
    echo "  → Copiando stdlib completo (optimizado)..."
    
    # Copiar todo el stdlib pero EXCLUIR directorios pesados innecesarios
    EXCLUDE_DIRS=(
        "test"           # Tests (muy pesado, ~50MB)
        "unittest"       # Framework de testing
        "distutils"      # Empaquetado (deprecated)
        "ensurepip"      # pip bootstrap
        "tkinter"        # GUI toolkit (no lo usamos)
        "turtle"         # Graphics (no lo usamos)
        "idlelib"        # IDLE IDE
        "lib2to3"        # 2to3 converter (deprecated)
        "pydoc_data"     # Documentación
        "__pycache__"    # Cache compilado (lo regeneraremos)
    )
    
    # Construir parámetros de exclusión para rsync
    RSYNC_EXCLUDE=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        RSYNC_EXCLUDE="$RSYNC_EXCLUDE --exclude=$dir"
    done
    
    # Usar rsync si está disponible (más eficiente), si no usar cp
    if command -v rsync &> /dev/null; then
        rsync -a $RSYNC_EXCLUDE "$PYTHON_STDLIB/" "$TARGET_STDLIB/"
        echo "  ✓ Stdlib copiado con rsync (excluidos: ${EXCLUDE_DIRS[*]})"
    else
        # Fallback: copiar todo y luego eliminar lo que no necesitamos
        cp -r "$PYTHON_STDLIB/"* "$TARGET_STDLIB/"
        
        # Eliminar directorios pesados
        for dir in "${EXCLUDE_DIRS[@]}"; do
            rm -rf "$TARGET_STDLIB/$dir" 2>/dev/null || true
        done
        
        echo "  ✓ Stdlib copiado con cp (excluidos: ${EXCLUDE_DIRS[*]})"
    fi
    
    # Limpiar archivos innecesarios adicionales
    echo "  → Limpiando archivos innecesarios..."
    
    # Eliminar archivos .pyc antiguos (se regenerarán)
    find "$TARGET_STDLIB" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Eliminar archivos .pyo (obsoletos en Python 3)
    find "$TARGET_STDLIB" -name "*.pyo" -delete 2>/dev/null || true
    
    # Eliminar archivos de desarrollo
    find "$TARGET_STDLIB" -name "*.c" -delete 2>/dev/null || true
    find "$TARGET_STDLIB" -name "*.h" -delete 2>/dev/null || true
    
    echo "  ✓ Limpieza completada"
    
    # Copiar lib-dynload (contiene módulos C compilados - CRÍTICO)
    if [ -d "$PYTHON_STDLIB/lib-dynload" ]; then
        mkdir -p "$TARGET_STDLIB/lib-dynload"
        cp -r "$PYTHON_STDLIB/lib-dynload/"* "$TARGET_STDLIB/lib-dynload/" 2>/dev/null || true
        echo "  ✓ Copiado lib-dynload (módulos C como _re, _json, etc.)"
    fi
    
    # Copiar config (puede ser necesario)
    for config_dir in "$PYTHON_STDLIB"/config-*; do
        if [ -d "$config_dir" ]; then
            cp -r "$config_dir" "$TARGET_STDLIB/"
            echo "  ✓ Copiado $(basename "$config_dir")"
        fi
    done
    
    STDLIB_SIZE=$(du -sh "$TARGET_STDLIB" 2>/dev/null | cut -f1)
    echo "  ✅ Stdlib listo: ~$STDLIB_SIZE"
else
    echo "  ⚠️ No se encontró stdlib en $PYTHON_STDLIB"
    echo "     El AppImage usará solo el venv (puede no funcionar)"
fi

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

# UTF-8 support
export LANG=\${LANG:-en_US.UTF-8}
export LC_ALL=\${LC_ALL:-en_US.UTF-8}

# Ejecutar aplicación
cd "\$APPDIR/usr/share/multiwall"
exec "\$APPDIR/usr/bin/python3" main.py "\$@"
EOF
chmod +x "$APP_DIR/AppRun"

echo "🧱 Creando archivo .desktop..."
cat > "$APP_DIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=AppRun
Icon=multiwall
Categories=Utility;
EOF

echo "🖼️ Copiando ícono..."
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
cp /app/appimage/icon.png "$APP_DIR/usr/share/icons/hicolor/256x256/apps/multiwall.png"
cp /app/appimage/icon.png "$APP_DIR/multiwall.png"


# Generar AppImage
echo ""
echo "🎁 Generando AppImage..."
cd /build

# Usar appimagetool extraído
ARCH=x86_64 /usr/local/bin/appimagetool.AppDir/AppRun "$APP_DIR" "/output/MultiWall-${VERSION}-x86_64.AppImage"

echo ""
echo "✅ AppImage creado: /output/MultiWall-${VERSION}-x86_64.AppImage"
ls -lh /output/*.AppImage