"""
UceAsistan Error Handler Module
Centralized exception handling and logging for the backend
"""

import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from functools import wraps
from typing import Callable, Any, Optional
import json

try:
    from config import settings
except ImportError:
    class FallbackSettings:
        LOG_LEVEL = "INFO"
        LOG_FILE = "logs/uceasistan.log"
        DEBUG = False
    settings = FallbackSettings()


# ============================================
# LOGGING SETUP
# ============================================

def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    
    # Create logs directory if it doesn't exist
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("uceasistan")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File Handler
    try:
        file_handler = logging.FileHandler(
            settings.LOG_FILE,
            encoding='utf-8',
            mode='a'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")
    
    return logger


# Global logger instance
logger = setup_logging()


# ============================================
# EXCEPTION CLASSES
# ============================================

class UceAsistanError(Exception):
    """Base exception for UceAsistan application."""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class MT5ConnectionError(UceAsistanError):
    """Raised when MT5 connection fails."""
    def __init__(self, message: str = "MT5 bağlantısı kurulamadı", details: dict = None):
        super().__init__(message, "MT5_CONNECTION_ERROR", details)


class AIProviderError(UceAsistanError):
    """Raised when AI provider request fails."""
    def __init__(self, message: str, provider: str = "unknown", details: dict = None):
        super().__init__(message, "AI_PROVIDER_ERROR", {"provider": provider, **(details or {})})


class BacktestError(UceAsistanError):
    """Raised when backtest execution fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "BACKTEST_ERROR", details)


class ValidationError(UceAsistanError):
    """Raised when input validation fails."""
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, **(details or {})})


class RateLimitError(UceAsistanError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit aşıldı", wait_seconds: int = 60):
        super().__init__(message, "RATE_LIMIT_ERROR", {"wait_seconds": wait_seconds})


class AuthenticationError(UceAsistanError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Kimlik doğrulama başarısız"):
        super().__init__(message, "AUTH_ERROR", {})


# ============================================
# DECORATORS
# ============================================

def handle_exceptions(default_return: Any = None):
    """
    Decorator to handle exceptions in functions.
    Logs the error and returns a default value or re-raises.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except UceAsistanError as e:
                logger.error(f"[{e.code}] {e.message}")
                if settings.DEBUG:
                    logger.debug(f"Details: {e.details}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                if settings.DEBUG:
                    logger.debug(traceback.format_exc())
                return default_return
        return wrapper
    return decorator


def async_handle_exceptions(default_return: Any = None):
    """
    Async version of exception handling decorator.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except UceAsistanError as e:
                logger.error(f"[{e.code}] {e.message}")
                if settings.DEBUG:
                    logger.debug(f"Details: {e.details}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                if settings.DEBUG:
                    logger.debug(traceback.format_exc())
                return default_return
        return wrapper
    return decorator


# ============================================
# ERROR RESPONSE HELPERS
# ============================================

def create_error_response(
    message: str,
    code: str = "ERROR",
    details: dict = None,
    response_type: str = "error"
) -> dict:
    """Create a standardized error response for WebSocket messages."""
    return {
        "type": response_type,
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
    }


def create_success_response(
    data: Any,
    response_type: str = "success",
    message: str = None
) -> dict:
    """Create a standardized success response for WebSocket messages."""
    response = {
        "type": response_type,
        "success": True,
        "data": data
    }
    if message:
        response["message"] = message
    return response


# ============================================
# WEBSOCKET ERROR HANDLER
# ============================================

async def safe_websocket_send(websocket, message: dict) -> bool:
    """
    Safely send a message through WebSocket.
    Returns True if successful, False otherwise.
    """
    try:
        import json
        await websocket.send(json.dumps(message, ensure_ascii=False))
        return True
    except Exception as e:
        logger.warning(f"Failed to send WebSocket message: {e}")
        return False


async def websocket_error_handler(websocket, error: Exception, action: str = None) -> None:
    """
    Handle WebSocket errors by sending appropriate error response.
    """
    if isinstance(error, UceAsistanError):
        response = create_error_response(
            message=error.message,
            code=error.code,
            details=error.details,
            response_type=f"{action}_error" if action else "error"
        )
    else:
        response = create_error_response(
            message=str(error),
            code="INTERNAL_ERROR",
            response_type=f"{action}_error" if action else "error"
        )
    
    await safe_websocket_send(websocket, response)


# ============================================
# STARTUP VALIDATION
# ============================================

def validate_environment() -> list[str]:
    """
    Validate the runtime environment and return list of issues.
    """
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        issues.append(f"Python 3.10+ required, found {sys.version}")
    
    # Check required packages
    required_packages = ['websockets', 'pandas', 'numpy', 'aiohttp']
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            issues.append(f"Missing required package: {pkg}")
    
    # Check MT5 availability
    try:
        from mt5_proxy import mt5, MT5_AVAILABLE
        if MT5_AVAILABLE:
            if not mt5.initialize():
                issues.append("MT5 terminal not accessible")
                mt5.shutdown()
        else:
            issues.append("MetaTrader5 package not compatible/installed (Running in Simulation Mode)")
    except Exception as e:
        issues.append(f"MT5 check failed: {e}")
    
    return issues


# ============================================
# LOG UTILITIES
# ============================================

def log_action(action: str, details: dict = None):
    """Log a user action for analytics."""
    log_entry = {
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    logger.info(f"ACTION: {action} | {details or ''}")


def log_performance(operation: str, duration_ms: float):
    """Log performance metrics."""
    logger.debug(f"PERF: {operation} completed in {duration_ms:.2f}ms")


# Export all
__all__ = [
    'logger',
    'setup_logging',
    'UceAsistanError',
    'MT5ConnectionError',
    'AIProviderError',
    'BacktestError',
    'ValidationError',
    'RateLimitError',
    'AuthenticationError',
    'handle_exceptions',
    'async_handle_exceptions',
    'create_error_response',
    'create_success_response',
    'safe_websocket_send',
    'websocket_error_handler',
    'validate_environment',
    'log_action',
    'log_performance'
]
