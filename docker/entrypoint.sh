#!/usr/bin/env bash
set -e

cd /app

# Asegurar que el usuario tenga permisos en el directorio
if [ -w /app ]; then
    # Crear entorno virtual si no existe
    if [ ! -d ".venv" ]; then
        echo "🔧 Creando entorno virtual..."
        python -m venv .venv
        source .venv/bin/activate
        python -m ensurepip --upgrade
        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt
    else
        echo "✅ Usando entorno virtual existente"
        source .venv/bin/activate
    fi
else
    echo "⚠️ Sin permisos de escritura en /app, usando venv existente"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "❌ No existe entorno virtual y no se puede crear"
        exit 1
    fi
fi

# Asegurar que el directorio de configuración existe y tiene permisos
CONFIG_DIR="$HOME/.config/multiwall"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "📁 Creando directorio de configuración: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR" 2>/dev/null || true
fi

echo "🚀 Ejecutando: $@"
exec "$@"