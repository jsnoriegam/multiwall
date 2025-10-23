import json
from pathlib import Path
from .logger import get_logger

logger = get_logger(__name__)

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
        CONFIG_DIR.chmod(0o755)
        logger.info(f"Config directory: {CONFIG_DIR}")
        return True
    except Exception as e:
        logger.error(f"Error creating config directory: {e}")
        return False


def load_config():
    """Carga la configuración desde el archivo JSON."""
    if CONFIG_FILE.exists():
        try:
            content = CONFIG_FILE.read_text()
            config = json.loads(content)
            logger.info(f"Configuration loaded from: {CONFIG_FILE}")
            return config
        except Exception as e:
            logger.error(f"Error reading configuration: {e}")
            return {}
    logger.info(f"No previous configuration at: {CONFIG_FILE}")
    return {}


def save_config(cfg):
    """Guarda la configuración en el archivo JSON."""
    if not ensure_config_dir():
        logger.error("Could not create config directory")
        return False
    
    try:
        # Convertir a JSON con formato legible
        json_content = json.dumps(cfg, indent=2, ensure_ascii=False)
        
        # Guardar en el archivo
        CONFIG_FILE.write_text(json_content, encoding='utf-8')
        
        # Verificar que se guardó correctamente
        if CONFIG_FILE.exists():
            logger.info(f"Configuration saved successfully to: {CONFIG_FILE}")
            logger.debug(f"File size: {CONFIG_FILE.stat().st_size} bytes")
            return True
        else:
            logger.error(f"File was not created: {CONFIG_FILE}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        return False