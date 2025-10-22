#!/bin/bash
set -e

echo "🔨 Construyendo MultiWall Flatpak..."

APP_ID="com.latinosoft.MultiWall"
BUILD_DIR="/build/flatpak-build"
REPO_DIR="/build/flatpak-repo"

# Crear directorios
mkdir -p "$BUILD_DIR"
mkdir -p "$REPO_DIR"

# Construir Flatpak con acceso a red
echo "📦 Construyendo con flatpak-builder..."
flatpak-builder \
    --force-clean \
    --repo="$REPO_DIR" \
    --install-deps-from=flathub \
    --ccache \
    --require-changes \
    --allow-missing-runtimes \
    "$BUILD_DIR" \
    /app/flatpak/${APP_ID}.yml

# Crear bundle (archivo .flatpak)
echo "🎁 Creando bundle..."
flatpak build-bundle \
    "$REPO_DIR" \
    "/output/MultiWall.flatpak" \
    "$APP_ID"

echo "✅ Flatpak creado: /output/MultiWall.flatpak"
ls -lh /output/*.flatpak