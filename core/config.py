import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

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

    @field_validator('max_file_size', 'max_upload_size', mode='before')
    @classmethod
    def parse_int_with_strip(cls, v):
        """Strip whitespace and newlines from integer fields"""
        if isinstance(v, str):
            return int(v.strip())
        return v

    # Processing Settings
    max_pages_ocr: int = 5
    ocr_confidence_threshold: float = 0.7

    # AI/Gemini Settings (if using)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"

    # Storage Settings
    results_dir: str = "results"
    temp_dir: str = "temp"
    
    # Google Search API Settings (for LinkedIn verification)
    google_search_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    use_selenium_verification: bool = False  # Disabled - search engines block Browserless

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
