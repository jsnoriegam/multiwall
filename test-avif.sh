#!/bin/bash
set -e

echo "🧪 Testing AVIF Support in AppImage"
echo "===================================="

# Encontrar el AppImage
APPIMAGE=$(ls dist/MultiWall-*.AppImage 2>/dev/null | head -1)

if [ -z "$APPIMAGE" ]; then
    echo "❌ No AppImage found in dist/"
    exit 1
fi

echo "📦 Found AppImage: $APPIMAGE"
echo ""

# Hacer ejecutable
chmod +x "$APPIMAGE"

# Extraer el AppImage para inspección
echo "📂 Extracting AppImage for inspection..."
EXTRACT_DIR="/tmp/multiwall_appimage_test"
rm -rf "$EXTRACT_DIR"
"$APPIMAGE" --appimage-extract >/dev/null 2>&1
mv squashfs-root "$EXTRACT_DIR"

echo "✅ AppImage extracted to: $EXTRACT_DIR"
echo ""

# Verificar estructura
echo "📋 Checking AppImage structure..."
echo "  Python venv: $([ -d "$EXTRACT_DIR/usr/venv" ] && echo '✅' || echo '❌')"
echo "  Libraries: $([ -d "$EXTRACT_DIR/usr/lib/x86_64-linux-gnu" ] && echo '✅' || echo '❌')"
echo "  Application: $([ -d "$EXTRACT_DIR/usr/share/multiwall" ] && echo '✅' || echo '❌')"
echo ""

# Verificar librerías AVIF
echo "🔍 Checking AVIF libraries..."
cd "$EXTRACT_DIR/usr/lib/x86_64-linux-gnu"
for lib in libavif libaom libdav1d libheif; do
    if ls ${lib}*.so* >/dev/null 2>&1; then
        count=$(ls ${lib}*.so* | wc -l)
        echo "  ✅ $lib: $count file(s)"
    else
        echo "  ❌ $lib: NOT FOUND"
    fi
done
echo ""

# Probar Python y Pillow dentro del AppImage
echo "🐍 Testing Python and Pillow inside AppImage..."
cd "$EXTRACT_DIR"

# Activar el venv y probar
export PYTHONPATH="$EXTRACT_DIR/usr/share/multiwall:$EXTRACT_DIR/usr/venv/lib/python3.12/site-packages"
export LD_LIBRARY_PATH="$EXTRACT_DIR/usr/lib/x86_64-linux-gnu:$EXTRACT_DIR/usr/lib"
source "$EXTRACT_DIR/usr/venv/bin/activate"

python3 << 'EOF'
import sys
from PIL import Image, features

print("="*60)
print("PILLOW CONFIGURATION IN APPIMAGE")
print("="*60)
print(f"Python: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Pillow version: {Image.__version__}")
print()

# Verificar features
print("Features:")
for feature in ['webp', 'webp_anim', 'webp_mux', 'libjpeg_turbo', 'avif']:
    try:
        supported = features.check(feature)
        status = "✅" if supported else "❌"
        print(f"  {status} {feature}: {supported}")
    except Exception as e:
        print(f"  ❓ {feature}: Error - {e}")

print()

# Verificar extensiones
extensions = Image.registered_extensions()
avif_exts = [ext for ext in extensions.keys() if 'avif' in ext]
print(f"AVIF extensions registered: {avif_exts if avif_exts else '❌ NONE'}")

print()

# Intentar cargar un archivo AVIF de prueba (si existe)
import os
test_files = [
    os.path.expanduser("~/Imágenes/Wallpapers/bg_1.avif"),
    os.path.expanduser("~/Pictures/test.avif"),
]

for test_file in test_files:
    if os.path.exists(test_file):
        print(f"Testing with: {test_file}")
        try:
            img = Image.open(test_file)
            print(f"  ✅ SUCCESS: {img.format}, {img.mode}, {img.size}")
            break
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
    else:
        print(f"  ⏭️  Skipping (not found): {test_file}")

print("="*60)
EOF

echo ""
echo "🧹 Cleaning up..."
rm -rf "$EXTRACT_DIR"

echo ""
echo "✅ Test complete!"
echo ""
echo "📝 Next steps:"
echo "  1. If AVIF support is ✅, rebuild the AppImage"
echo "  2. If AVIF support is ❌, check the build logs"
echo "  3. Run the AppImage with: DEBUG_APPIMAGE=1 $APPIMAGE"