"""
Sistema de logging para MultiWall.
Proporciona logging a archivo y consola con niveles configurables.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Mantener registro de loggers ya configurados
_configured_loggers = set()

def setup_logger(name, level=logging.INFO):
    """Configura un logger con nombre y nivel específicos."""
    logger = logging.getLogger(name)
    
    # Si el logger ya fue configurado, solo actualizar nivel
    if name in _configured_loggers:
        logger.setLevel(level)
        return logger
    
    # Marcar logger como configurado
    _configured_loggers.add(name)
    
    # Configurar logger solo si no tiene handlers
    if not logger.handlers:
        logger.setLevel(level)
        
        # Crear handler para stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Crear formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Agregar handler al logger
        logger.addHandler(handler)
        
        # Handler para archivo (opcional, solo si se puede escribir)
        try:
            log_dir = Path.home() / ".config" / "multiwall" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Nombre de archivo con fecha
            log_file = log_dir / f"multiwall_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # Archivo siempre en DEBUG
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_file}")
            
        except Exception as e:
            logger.warning(f"Could not create log file: {e}")
    
    return logger

def get_logger(name):
    """Obtiene un logger ya configurado o crea uno nuevo."""
    return logging.getLogger(name)


# Logger por defecto para importación rápida
logger = get_logger(__name__)