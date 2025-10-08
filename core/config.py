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

    # Database Settings
    # Use absolute path for SQLite to avoid WSL/Windows filesystem issues
    database_url: str = "sqlite+aiosqlite:////tmp/hr_recruitment.db"  # Default to SQLite for dev
    
    # Redis Settings
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT Settings
    jwt_secret_key: str = "dev-secret-key-change-in-production-use-secrets-token-urlsafe-32"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    
    # Email Settings (SendGrid)
    sendgrid_api_key: Optional[str] = None
    sender_email: str = "noreply@hrrecruitment.com"
    sender_name: str = "HR Recruitment System"
    
    # Frontend URL (for email links)
    frontend_url: str = "http://localhost:8000"
    # Security Settings
    password_min_length: int = 8
    account_lockout_attempts: int = 5
    account_lockout_duration_minutes: int = 15
    password_history_count: int = 5
    
    # Resume Upload Settings
    resume_upload_dir: str = "uploads/resumes"
    max_resume_size: int = 10 * 1024 * 1024  # 10MB
    allowed_resume_formats: list = [".pdf", ".docx", ".txt"]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
