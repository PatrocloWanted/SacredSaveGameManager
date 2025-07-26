"""Centralized logging system for Sacred Save Game Manager."""

import logging
import logging.handlers
import os
import pathlib
from datetime import datetime
from typing import Optional, Dict, Any


class AppLogger:
    """Centralized logging manager for the application."""
    
    _instance: Optional['AppLogger'] = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls) -> 'AppLogger':
        """Singleton pattern to ensure one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logging system."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.log_dir = pathlib.Path("logs")
            self.log_dir.mkdir(exist_ok=True)
            self._setup_root_logger()
    
    def _setup_root_logger(self) -> None:
        """Set up the root logger configuration."""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        log_file = self.log_dir / "sacred_manager.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB files, keep 5 backups
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Error file handler (separate file for errors)
        error_file = self.log_dir / "sacred_manager_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3  # 5MB files, keep 3 backups
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger('sacred_manager')
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(error_handler)
        
        # Prevent duplicate logs
        root_logger.propagate = False
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module."""
        full_name = f"sacred_manager.{name}"
        
        if full_name not in self._loggers:
            logger = logging.getLogger(full_name)
            self._loggers[full_name] = logger
        
        return self._loggers[full_name]
    
    def log_operation(self, logger_name: str, operation: str, details: Dict[str, Any] = None) -> None:
        """Log a successful operation with details."""
        logger = self.get_logger(logger_name)
        details_str = f" - Details: {details}" if details else ""
        logger.info(f"Operation: {operation}{details_str}")
    
    def log_error(self, logger_name: str, error: Exception, context: str, details: Dict[str, Any] = None) -> None:
        """Log an error with context and details."""
        logger = self.get_logger(logger_name)
        details_str = f" - Details: {details}" if details else ""
        logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}{details_str}", exc_info=True)
    
    def log_warning(self, logger_name: str, message: str, details: Dict[str, Any] = None) -> None:
        """Log a warning message."""
        logger = self.get_logger(logger_name)
        details_str = f" - Details: {details}" if details else ""
        logger.warning(f"{message}{details_str}")
    
    def log_debug(self, logger_name: str, message: str, details: Dict[str, Any] = None) -> None:
        """Log a debug message."""
        logger = self.get_logger(logger_name)
        details_str = f" - Details: {details}" if details else ""
        logger.debug(f"{message}{details_str}")
    
    def log_user_action(self, action: str, details: Dict[str, Any] = None) -> None:
        """Log user actions for audit trail."""
        logger = self.get_logger("user_actions")
        details_str = f" - {details}" if details else ""
        logger.info(f"User Action: {action}{details_str}")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True, error: Exception = None) -> None:
        """Log file operations with success/failure status."""
        logger = self.get_logger("file_operations")
        if success:
            logger.info(f"File Operation Success: {operation} - {file_path}")
        else:
            error_msg = f": {str(error)}" if error else ""
            logger.error(f"File Operation Failed: {operation} - {file_path}{error_msg}")
    
    def log_config_change(self, change_type: str, details: Dict[str, Any]) -> None:
        """Log configuration changes."""
        logger = self.get_logger("config")
        logger.info(f"Config Change: {change_type} - {details}")
    
    def log_startup(self, version: str = "unknown") -> None:
        """Log application startup."""
        logger = self.get_logger("app")
        logger.info(f"Sacred Save Game Manager started - Version: {version}")
        logger.info(f"Log directory: {self.log_dir.absolute()}")
    
    def log_shutdown(self) -> None:
        """Log application shutdown."""
        logger = self.get_logger("app")
        logger.info("Sacred Save Game Manager shutting down")


# Global logger instance
app_logger = AppLogger()


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger."""
    return app_logger.get_logger(name)


def log_operation(logger_name: str, operation: str, details: Dict[str, Any] = None) -> None:
    """Convenience function to log operations."""
    app_logger.log_operation(logger_name, operation, details)


def log_error(logger_name: str, error: Exception, context: str, details: Dict[str, Any] = None) -> None:
    """Convenience function to log errors."""
    app_logger.log_error(logger_name, error, context, details)


def log_warning(logger_name: str, message: str, details: Dict[str, Any] = None) -> None:
    """Convenience function to log warnings."""
    app_logger.log_warning(logger_name, message, details)


def log_user_action(action: str, details: Dict[str, Any] = None) -> None:
    """Convenience function to log user actions."""
    app_logger.log_user_action(action, details)
