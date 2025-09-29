import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    app_name: str = "AI Powered HR Assistant"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # File Upload Settings
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    max_file_size: int = 10 * 1024 * 1024  # 10MB (alias for compatibility)
    allowed_extensions: list = [".pdf", ".doc", ".docx"]
    upload_dir: str = "uploads"

    # Processing Settings
    max_pages_ocr: int = 5
    ocr_confidence_threshold: float = 0.7

    # AI/Gemini Settings (if using)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"

    # Storage Settings
    results_dir: str = "results"
    temp_dir: str = "temp"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
