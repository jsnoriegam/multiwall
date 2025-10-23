"""
Logging system for MultiWall.
Provides file and console logging with configurable levels.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Keep track of configured loggers
_configured_loggers = set()

def setup_logger(name, level=logging.INFO):
    """
    Configure a logger with specific name and level.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger already configured, just update level
    if name in _configured_loggers:
        logger.setLevel(level)
        return logger
    
    # Mark logger as configured
    _configured_loggers.add(name)
    
    # Configure logger only if it has no handlers
    if not logger.handlers:
        logger.setLevel(level)
        
        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Formatter with colors for console (if supported)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional, only if writable)
        try:
            log_dir = Path.home() / ".config" / "multiwall" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Log file with date
            log_file = log_dir / f"multiwall_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # File always in DEBUG
            
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_file}")
            
        except Exception as e:
            logger.warning(f"Could not create log file: {e}")
    
    return logger


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name if terminal supports it
        if sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def get_logger(name):
    """
    Get an already configured logger or create a new one.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


# Default logger for quick import
logger = get_logger(__name__)