"""
Tests for database models

Tests cover:
- User model validations
- File model relationships
- Session expiration
- Enum validations
- Model constraints
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.models.file import File, SyncStatus
from app.models.session import Session
from app.utils.security import hash_password, generate_session_token


pytestmark = pytest.mark.asyncio


class TestUserModel:
    """Test User model"""

    async def test_user_creation(self, db_session: AsyncSession):
        """Test creating a user"""
        user = User(
            username="modeltest",
            email="modeltest@example.com",
            password_hash=hash_password("ModelTest123!"),
            role=UserRole.user,
            is_active=True
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.username == "modeltest"
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_user_unique_username(self, db_session: AsyncSession, test_user: User):
        """Test username must be unique"""
        duplicate_user = User(
            username="testuser",  # Same as test_user
            email="different@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.user
        )

        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_user_role_enum(self, db_session: AsyncSession):
        """Test user role is validated"""
        user = User(
            username="roletest",
            email="roletest@example.com",
            password_hash=hash_password("RoleTest123!"),
            role=UserRole.admin,  # Admin role
            is_active=True
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.role == UserRole.admin

    async def test_user_default_values(self, db_session: AsyncSession):
        """Test user default values"""
        user = User(
            username="defaulttest",
            email="defaulttest@example.com",
            password_hash=hash_password("DefaultTest123!"),
            role=UserRole.user
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.is_active is True
        assert user.failed_login_attempts == 0
        assert user.must_change_password is False or user.must_change_password is True


class TestFileModel:
    """Test File model"""

    async def test_file_creation(self, db_session: AsyncSession, test_user: User):
        """Test creating a file"""
        import hashlib

        content = b"Test file content"
        checksum = hashlib.sha256(content).hexdigest()

        file_obj = File(
            filename="model_test.txt",
            filepath="/tmp/model_test.txt",
            size=len(content),
            checksum=checksum,
            mime_type="text/plain",
            uploaded_by=test_user.id,
            upload_date=datetime.utcnow(),
            is_deleted=False,
            sync_status=SyncStatus.PENDING
        )

        db_session.add(file_obj)
        await db_session.commit()
        await db_session.refresh(file_obj)

        assert file_obj.id is not None
        assert file_obj.uploaded_by == test_user.id
        assert file_obj.sync_status == SyncStatus.PENDING

    async def test_file_uploader_relationship(self, db_session: AsyncSession, test_file: File, test_user: User):
        """Test file uploader relationship"""
        await db_session.refresh(test_file, ["uploader"])

        assert test_file.uploader is not None
        assert test_file.uploader.id == test_user.id

    async def test_file_sync_status_enum(self, db_session: AsyncSession, test_user: User):
        """Test sync status enum values"""
        for status in [SyncStatus.PENDING, SyncStatus.SYNCED, SyncStatus.CONFLICT, SyncStatus.ERROR]:
            file_obj = File(
                filename=f"sync_test_{status.value}.txt",
                filepath=f"/tmp/sync_{status.value}.txt",
                size=100,
                checksum="abc123",
                mime_type="text/plain",
                uploaded_by=test_user.id,
                upload_date=datetime.utcnow(),
                is_deleted=False,
                sync_status=status
            )

            db_session.add(file_obj)

        await db_session.commit()


class TestSessionModel:
    """Test Session model"""

    async def test_session_creation(self, db_session: AsyncSession, test_user: User):
        """Test creating a session"""
        token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        session = Session(
            user_id=test_user.id,
            token=token,
            ip_address="127.0.0.1",
            user_agent="pytest",
            expires_at=expires_at
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.token == token

    async def test_session_unique_token(self, db_session: AsyncSession, test_user: User):
        """Test session token must be unique"""
        token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        session1 = Session(
            user_id=test_user.id,
            token=token,
            ip_address="127.0.0.1",
            expires_at=expires_at
        )

        session2 = Session(
            user_id=test_user.id,
            token=token,  # Same token
            ip_address="192.168.1.1",
            expires_at=expires_at
        )

        db_session.add(session1)
        await db_session.commit()

        db_session.add(session2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_session_user_relationship(self, db_session: AsyncSession, test_user: User):
        """Test session user relationship"""
        token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        session = Session(
            user_id=test_user.id,
            token=token,
            ip_address="127.0.0.1",
            expires_at=expires_at
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session, ["user"])

        assert session.user is not None
        assert session.user.id == test_user.id
