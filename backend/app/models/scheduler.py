"""Scheduler models"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Task execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    CANCELLED = "cancelled"


class ScheduledTask(Base):
    """Scheduled task model"""
    __tablename__ = "scheduled_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_name = Column(String(100), unique=True, nullable=False)
    task_type = Column(String(50), nullable=False)
    cron_expression = Column(String(50), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(Enum(TaskStatus), nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    execution_history = relationship("TaskExecutionHistory", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScheduledTask {self.task_name}>"


class TaskExecutionHistory(Base):
    """Task execution history model"""
    __tablename__ = "task_execution_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("scheduled_tasks.id"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(Enum(TaskStatus), nullable=False)
    error_message = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)
    triggered_by = Column(String(50), nullable=False)  # 'system' or 'manual' or user_id

    # Relationships
    task = relationship("ScheduledTask", back_populates="execution_history")

    def __repr__(self):
        return f"<TaskExecutionHistory {self.task_id} - {self.status}>"
