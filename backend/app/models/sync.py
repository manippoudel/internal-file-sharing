"""Sync models"""
import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database import Base


class SyncType(str, enum.Enum):
    """Sync direction enumeration"""
    WIN_TO_UBUNTU = "win_to_ubuntu"
    UBUNTU_TO_WIN = "ubuntu_to_win"


class SyncLogStatus(str, enum.Enum):
    """Sync status enumeration"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    RUNNING = "running"


class SyncLog(Base):
    """Sync log model for tracking sync operations"""
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_type = Column(Enum(SyncType), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    files_synced = Column(Integer, default=0, nullable=False)
    bytes_transferred = Column(BigInteger, default=0, nullable=False)
    status = Column(Enum(SyncLogStatus), nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<SyncLog {self.sync_type} - {self.status}>"


class UploadChunk(Base):
    """Upload chunk model for chunked file uploads"""
    __tablename__ = "upload_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    total_chunks = Column(Integer, nullable=False)
    chunk_number = Column(Integer, nullable=False)
    chunk_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    file_path = Column(String(500), nullable=False)

    def __repr__(self):
        return f"<UploadChunk {self.upload_id} - {self.chunk_number}/{self.total_chunks}>"
