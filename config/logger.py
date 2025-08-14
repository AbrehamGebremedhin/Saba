"""
Universal logger configuration for the Saba application.
Provides centralized logging with different levels and formatters.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional

class SabaLogger:
    """Universal logger for the Saba application."""
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_root_logger()
        return cls._instance
    
    def _setup_root_logger(self):
        """Setup the root logger configuration."""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger('saba')
        root_logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f'saba_{datetime.now().strftime("%Y%m%d")}.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Error file handler for errors only
        error_handler = logging.FileHandler(
            os.path.join(log_dir, f'saba_errors_{datetime.now().strftime("%Y%m%d")}.log'),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Add handlers to root logger
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
        # Prevent propagation to avoid duplicate logs
        root_logger.propagate = False
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name.
        
        Args:
            name: Logger name (usually __name__ of the module)
            
        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            # Create child logger
            logger = logging.getLogger(f'saba.{name}')
            self._loggers[name] = logger
        
        return self._loggers[name]


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format the log record with colors."""
        # Save original levelname
        original_levelname = record.levelname
        
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        return formatted


# Global logger instance
_saba_logger = SabaLogger()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Logger name (usually __name__ of the module)
              If None, uses the calling module's name
        
    Returns:
        Configured logger instance
    """
    if name is None:
        # Get the caller's module name
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', 'unknown')
        # Remove 'saba.' prefix if present
        if name.startswith('saba.'):
            name = name[5:]
    
    return _saba_logger.get_logger(name)


def set_log_level(level: str):
    """
    Set the logging level for all loggers.
    
    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    root_logger = logging.getLogger('saba')
    root_logger.setLevel(numeric_level)
    
    # Update console handler level (keep file handlers as they are)
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(numeric_level)