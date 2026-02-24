"""
Tests for audit logging service

Tests cover:
- Actions are logged with user/IP/timestamp
- Filter logs by user
- Filter logs by action type
- Filter logs by date range
- Logs include request details
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit_service import AuditService
from app.models.audit import AuditLog
from app.models.user import User


pytestmark = pytest.mark.asyncio


class TestAuditService:
    """Test audit logging service"""

    async def test_log_action(self, db_session: AsyncSession, test_user: User):
        """Test logging an action"""
        await AuditService.log_action(
            db=db_session,
            user_id=test_user.id,
            action="test_action",
            ip_address="127.0.0.1",
            user_agent="pytest",
            details={"test_key": "test_value"}
        )

        # Verify log was created
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.user_id == test_user.id)
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.action == "test_action"
        assert log.ip_address == "127.0.0.1"
        assert log.user_agent == "pytest"

    async def test_log_action_without_user(self, db_session: AsyncSession):
        """Test logging system actions without user"""
        await AuditService.log_action(
            db=db_session,
            user_id=None,
            action="system_action",
            ip_address="0.0.0.0",
            details={"type": "automated"}
        )

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "system_action")
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.user_id is None

    async def test_get_logs_all(self, db_session: AsyncSession, test_user: User):
        """Test retrieving all logs"""
        # Create some logs
        for i in range(3):
            await AuditService.log_action(
                db=db_session,
                user_id=test_user.id,
                action=f"action_{i}",
                ip_address="127.0.0.1"
            )

        logs, total = await AuditService.get_logs(db=db_session)

        assert total >= 3
        assert len(logs) >= 3

    async def test_get_logs_filter_by_user(self, db_session: AsyncSession, test_user: User, admin_user: User):
        """Test filtering logs by user"""
        # Create logs for different users
        await AuditService.log_action(
            db=db_session,
            user_id=test_user.id,
            action="user_action",
            ip_address="127.0.0.1"
        )

        await AuditService.log_action(
            db=db_session,
            user_id=admin_user.id,
            action="admin_action",
            ip_address="127.0.0.1"
        )

        # Filter by test_user
        logs, total = await AuditService.get_logs(
            db=db_session,
            user_id=test_user.id
        )

        assert total >= 1
        assert all(log.user_id == test_user.id for log in logs)

    async def test_get_logs_filter_by_action(self, db_session: AsyncSession, test_user: User):
        """Test filtering logs by action type"""
        await AuditService.log_action(
            db=db_session,
            user_id=test_user.id,
            action="login",
            ip_address="127.0.0.1"
        )

        await AuditService.log_action(
            db=db_session,
            user_id=test_user.id,
            action="file_upload",
            ip_address="127.0.0.1"
        )

        # Filter by action
        logs, total = await AuditService.get_logs(
            db=db_session,
            action="login"
        )

        assert total >= 1
        assert all(log.action == "login" for log in logs)

    async def test_get_logs_filter_by_date_range(self, db_session: AsyncSession, test_user: User):
        """Test filtering logs by date range"""
        now = datetime.utcnow()

        await AuditService.log_action(
            db=db_session,
            user_id=test_user.id,
            action="recent_action",
            ip_address="127.0.0.1"
        )

        # Filter by date range (today)
        logs, total = await AuditService.get_logs(
            db=db_session,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1)
        )

        assert total >= 1

    async def test_get_logs_pagination(self, db_session: AsyncSession, test_user: User):
        """Test log pagination"""
        # Create multiple logs
        for i in range(10):
            await AuditService.log_action(
                db=db_session,
                user_id=test_user.id,
                action=f"action_{i}",
                ip_address="127.0.0.1"
            )

        # Get first page
        logs_page1, total = await AuditService.get_logs(
            db=db_session,
            page=1,
            page_size=5
        )

        assert len(logs_page1) <= 5
        assert total >= 10

        # Get second page
        logs_page2, _ = await AuditService.get_logs(
            db=db_session,
            page=2,
            page_size=5
        )

        assert len(logs_page2) <= 5
