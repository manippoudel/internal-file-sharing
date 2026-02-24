"""Database models"""
# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User, UserRole
from app.models.session import Session
from app.models.file import File, SyncStatus
from app.models.audit import AuditLog
from app.models.sync import SyncLog, SyncType, SyncLogStatus
from app.models.settings import SystemSetting
from app.models.scheduler import ScheduledTask, TaskExecutionHistory, TaskStatus

__all__ = [
    "User",
    "UserRole",
    "Session",
    "File",
    "SyncStatus",
    "AuditLog",
    "SyncLog",
    "SyncType",
    "SyncLogStatus",
    "SystemSetting",
    "ScheduledTask",
    "TaskExecutionHistory",
    "TaskStatus",
]

