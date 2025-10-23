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
    """Ensure configuration directory exists with correct permissions."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_DIR.chmod(0o755)
        logger.debug(f"Config directory ensured: {CONFIG_DIR}")
        return True
    except Exception as e:
        logger.error(f"Error creating config directory: {e}")
        return False


def load_config():
    """
    Load configuration from JSON file.
    
    Returns:
        dict: Configuration dictionary or empty dict if not found
    """
    if CONFIG_FILE.exists():
        try:
            content = CONFIG_FILE.read_text(encoding='utf-8')
            config = json.loads(content)
            logger.info(f"Configuration loaded: {CONFIG_FILE}")
            logger.debug(f"Loaded {len(config.get('monitors', {}))} monitor configurations")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading configuration: {e}")
            return {}
    
    logger.info(f"No previous configuration found at: {CONFIG_FILE}")
    return {}


def save_config(cfg):
    """
    Save configuration to JSON file.
    
    Args:
        cfg: Configuration dictionary to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    if not ensure_config_dir():
        logger.error("Could not create config directory")
        return False
    
    try:
        # Convert to JSON with readable format
        json_content = json.dumps(cfg, indent=2, ensure_ascii=False)
        
        # Save to file
        CONFIG_FILE.write_text(json_content, encoding='utf-8')
        
        # Verify save was successful
        if CONFIG_FILE.exists():
            file_size = CONFIG_FILE.stat().st_size
            logger.info(f"Configuration saved: {CONFIG_FILE} ({file_size} bytes)")
            logger.debug(f"Saved {len(cfg.get('monitors', {}))} monitor configurations")
            return True
        else:
            logger.error(f"File was not created: {CONFIG_FILE}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        return False