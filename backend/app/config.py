"""Application configuration and settings"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Internal File Sharing System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/filedb"
    
    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    SESSION_EXPIRE_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 * 1024  # 10 GB
    CHUNK_SIZE: int = 50 * 1024 * 1024  # 50 MB
    MAX_CONCURRENT_UPLOADS: int = 3
    MAX_CONCURRENT_DOWNLOADS: int = 5
    
    # File Storage
    STORAGE_PATH: str = "/data"
    ACTIVE_FILES_PATH: str = "/data/active"
    DELETED_FILES_PATH: str = "/data/deleted"
    TEMP_FILES_PATH: str = "/data/temp"
    BACKUP_PATH: str = "/data/backups"
    LOGS_PATH: str = "/data/logs"
    
    # Sync Settings
    SYNC_ENABLED: bool = True
    RCLONE_CONFIG_PATH: str = "/etc/rclone/rclone.conf"
    WINDOWS_SERVER_PATH: str = "windows-remote:"
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True
    
    # File Retention
    DELETED_FILES_RETENTION_DAYS: int = 90
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 100
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Maximum concurrent users
    MAX_CONCURRENT_USERS: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
