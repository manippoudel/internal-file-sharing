"""File model"""
import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class SyncStatus(str, enum.Enum):
    """File sync status enumeration"""
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    ERROR = "error"


class File(Base):
    """File model for storing file metadata"""
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False, index=True)
    filepath = Column(String(500), nullable=False)
    size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256
    mime_type = Column(String(100), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.PENDING, nullable=False)

    # Relationships
    uploader = relationship("User", back_populates="uploaded_files", foreign_keys=[uploaded_by])
    deleter = relationship("User", back_populates="deleted_files", foreign_keys=[deleted_by])
    audit_logs = relationship("AuditLog", back_populates="target_file")

    def __repr__(self):
        return f"<File {self.filename}>"
