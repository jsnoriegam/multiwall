import json
from pathlib import Path


APP_NAME = "multiwall"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"


DEFAULT_OPTIONS = {
    "mode": "fill",
    "background": "#000000"
}


def ensure_config_dir():
    """Asegura que el directorio de configuración existe con permisos correctos."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Asegurar permisos de escritura
        CONFIG_DIR.chmod(0o755)
        print(f"Directorio de configuración: {CONFIG_DIR}")
        return True
    except Exception as e:
        print(f"Error creando directorio de configuración: {e}")
        return False


def load_config():
    """Carga la configuración desde el archivo JSON."""
    if CONFIG_FILE.exists():
        try:
            content = CONFIG_FILE.read_text()
            config = json.loads(content)
            print(f"Configuración cargada desde: {CONFIG_FILE}")
            return config
        except Exception as e:
            print(f"Error leyendo configuración: {e}")
            return {}
    print(f"No existe configuración previa en: {CONFIG_FILE}")
    return {}


def save_config(cfg):
    """Guarda la configuración en el archivo JSON."""
    if not ensure_config_dir():
        print("No se pudo crear el directorio de configuración")
        return False
    
    try:
        # Convertir a JSON con formato legible
        json_content = json.dumps(cfg, indent=2, ensure_ascii=False)
        
        # Guardar en el archivo
        CONFIG_FILE.write_text(json_content, encoding='utf-8')
        
        # Verificar que se guardó correctamente
        if CONFIG_FILE.exists():
            print(f"✅ Configuración guardada exitosamente en: {CONFIG_FILE}")
            print(f"   Tamaño: {CONFIG_FILE.stat().st_size} bytes")
            return True
        else:
            print(f"❌ El archivo no se creó: {CONFIG_FILE}")
            return False
            
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        import traceback
        traceback.print_exc()
        return False