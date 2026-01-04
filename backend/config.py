"""
UceAsistan Configuration Module
Centralized configuration management using Pydantic Settings

Usage:
    from config import settings
    print(settings.GROQ_API_KEY)
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Values can be overridden by a .env file in the backend directory.
    """
    
    # =========================================
    # SERVER CONFIGURATION
    # =========================================
    HOST: str = Field(default="localhost", description="WebSocket server host")
    PORT: int = Field(default=8766, description="WebSocket server port")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    
    # =========================================
    # AI PROVIDERS
    # =========================================
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    DEFAULT_AI_PROVIDER: str = Field(default="groq", description="Default AI provider")
    
    # =========================================
    # TELEGRAM NOTIFICATIONS
    # =========================================
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram bot token")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Telegram chat ID")
    TELEGRAM_ENABLED: bool = Field(default=False, description="Enable Telegram notifications")
    
    # =========================================
    # DATABASE
    # =========================================
    DATABASE_URL: str = Field(
        default="sqlite:///./uceasistan.db",
        description="Database connection URL"
    )
    
    # =========================================
    # AUTHENTICATION
    # =========================================
    JWT_SECRET: str = Field(
        default="change-me-in-production",
        description="JWT signing secret"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRY_HOURS: int = Field(default=24, description="JWT token expiry in hours")
    
    # =========================================
    # SUPABASE (Optional SaaS Auth)
    # =========================================
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(default="", description="Supabase anonymous key")
    
    # =========================================
    # RATE LIMITING
    # =========================================
    AI_RATE_LIMIT_CALLS: int = Field(default=20, description="Max AI calls per period")
    AI_RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit period in seconds")
    
    # =========================================
    # LOGGING
    # =========================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="logs/uceasistan.log", description="Log file path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    # =========================================
    # HELPER METHODS
    # =========================================
    def get_ai_key(self, provider: Optional[str] = None) -> str:
        """Get API key for specified or default AI provider."""
        provider = provider or self.DEFAULT_AI_PROVIDER
        provider = provider.lower()
        
        if provider == "groq":
            return self.GROQ_API_KEY
        elif provider == "openai":
            return self.OPENAI_API_KEY
        elif provider == "gemini":
            return self.GEMINI_API_KEY
        else:
            raise ValueError(f"Unknown AI provider: {provider}")
    
    def is_ai_configured(self, provider: Optional[str] = None) -> bool:
        """Check if AI provider is configured with an API key."""
        try:
            return bool(self.get_ai_key(provider))
        except ValueError:
            return False
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram is fully configured."""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)
    
    def is_supabase_configured(self) -> bool:
        """Check if Supabase is configured."""
        return bool(self.SUPABASE_URL and self.SUPABASE_ANON_KEY)
    
    def ensure_log_directory(self) -> None:
        """Create log directory if it doesn't exist."""
        log_path = Path(self.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Use this function to access settings throughout the application.
    """
    return Settings()


# Global settings instance
settings = get_settings()


# =========================================
# VALIDATION ON IMPORT
# =========================================
def validate_settings() -> list[str]:
    """
    Validate settings and return list of warnings.
    Called on application startup.
    """
    warnings = []
    
    if settings.JWT_SECRET == "change-me-in-production":
        warnings.append("[WARNING] JWT_SECRET is using default value. Set a secure secret in production!")
    
    if not settings.is_ai_configured():
        warnings.append("[WARNING] No AI provider configured. AI features will not work.")
    
    if settings.TELEGRAM_ENABLED and not settings.is_telegram_configured():
        warnings.append("[WARNING] Telegram is enabled but not fully configured.")
    
    return warnings


# Print warnings on import if in debug mode
if __name__ == "__main__" or os.getenv("DEBUG", "").lower() == "true":
    for warning in validate_settings():
        print(warning)
