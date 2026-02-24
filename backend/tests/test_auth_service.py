"""
Tests for authentication service

Tests cover:
- User creation with password hashing
- Successful login and session creation
- Failed login with wrong password
- Account lockout after max attempts
- Account auto-unlock after timeout
- Session validation
- Logout functionality
- Password change with validation
- Session cleanup
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.models.user import User, UserRole
from app.models.session import Session
from app.config import settings
from app.utils.security import verify_password


pytestmark = pytest.mark.asyncio


class TestAuthService:
    """Test authentication service"""

    async def test_create_user(self, db_session: AsyncSession):
        """Test user creation with password hashing"""
        user = await AuthService.create_user(
            db=db_session,
            username="newuser",
            password="NewUser123!",
            email="newuser@example.com",
            role=UserRole.user
        )

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role == UserRole.user
        assert user.is_active is True
        assert user.must_change_password is True
        assert user.password_hash != "NewUser123!"
        assert verify_password("NewUser123!", user.password_hash) is True

    async def test_create_admin_user(self, db_session: AsyncSession):
        """Test creating an admin user"""
        user = await AuthService.create_user(
            db=db_session,
            username="adminuser",
            password="AdminPassword123!",
            email="adminuser@example.com",
            role=UserRole.admin
        )

        assert user.role == UserRole.admin

    async def test_successful_login(self, db_session: AsyncSession, test_user: User):
        """Test successful authentication"""
        user, token, message = await AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="TestPassword123!",
            ip_address="127.0.0.1",
            user_agent="pytest-test"
        )

        assert user is not None
        assert user.id == test_user.id
        assert token is not None
        assert len(token) > 0
        assert message == "Login successful"
        assert user.failed_login_attempts == 0

        # Verify session was created
        result = await db_session.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()
        assert session is not None
        assert session.user_id == user.id
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "pytest-test"

    async def test_login_wrong_password(self, db_session: AsyncSession, test_user: User):
        """Test login with incorrect password"""
        user, token, message = await AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="WrongPassword123!",
            ip_address="127.0.0.1"
        )

        assert user is None
        assert token is None
        assert "Invalid username or password" in message

        # Verify failed attempt was recorded
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 1

    async def test_login_invalid_username(self, db_session: AsyncSession):
        """Test login with non-existent username"""
        user, token, message = await AuthService.authenticate_user(
            db=db_session,
            username="nonexistent",
            password="SomePassword123!",
            ip_address="127.0.0.1"
        )

        assert user is None
        assert token is None
        assert "Invalid username or password" in message

    async def test_account_lockout_after_max_attempts(self, db_session: AsyncSession, test_user: User):
        """Test account lockout after max failed login attempts"""
        # Make max_attempts failed logins
        for i in range(settings.MAX_LOGIN_ATTEMPTS):
            await AuthService.authenticate_user(
                db=db_session,
                username="testuser",
                password="WrongPassword123!",
                ip_address="127.0.0.1"
            )

        # Verify account is locked
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS
        assert test_user.locked_until is not None
        assert test_user.locked_until > datetime.utcnow()

        # Try to login with correct password - should fail
        user, token, message = await AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="TestPassword123!",
            ip_address="127.0.0.1"
        )

        assert user is None
        assert token is None
        assert "Account locked" in message or "Account is locked" in message

    async def test_locked_account_login(self, db_session: AsyncSession, locked_user: User):
        """Test login attempt with already locked account"""
        user, token, message = await AuthService.authenticate_user(
            db=db_session,
            username="lockeduser",
            password="LockedPassword123!",
            ip_address="127.0.0.1"
        )

        assert user is None
        assert token is None
        assert "locked" in message.lower()

    async def test_account_auto_unlock(self, db_session: AsyncSession):
        """Test account auto-unlock after lockout period"""
        # Create user with expired lock
        from app.utils.security import hash_password

        user = User(
            username="expiredlock",
            email="expired@example.com",
            password_hash=hash_password("ExpiredLock123!"),
            role=UserRole.user,
            is_active=True,
            failed_login_attempts=5,
            locked_until=datetime.utcnow() - timedelta(minutes=1)  # Expired lock
        )
        db_session.add(user)
        await db_session.commit()

        # Try to login - should succeed
        user_result, token, message = await AuthService.authenticate_user(
            db=db_session,
            username="expiredlock",
            password="ExpiredLock123!",
            ip_address="127.0.0.1"
        )

        assert user_result is not None
        assert token is not None
        assert message == "Login successful"
        assert user_result.failed_login_attempts == 0
        assert user_result.locked_until is None

    async def test_inactive_user_login(self, db_session: AsyncSession):
        """Test login with deactivated account"""
        from app.utils.security import hash_password

        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=hash_password("InactiveUser123!"),
            role=UserRole.user,
            is_active=False
        )
        db_session.add(inactive_user)
        await db_session.commit()

        user, token, message = await AuthService.authenticate_user(
            db=db_session,
            username="inactive",
            password="InactiveUser123!",
            ip_address="127.0.0.1"
        )

        assert user is None
        assert token is None
        assert "deactivated" in message.lower()

    async def test_validate_session_success(self, db_session: AsyncSession, test_user: User):
        """Test session validation with valid token"""
        # Login to create session
        user, token, _ = await AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="TestPassword123!",
            ip_address="127.0.0.1"
        )

        # Validate session
        validated_user = await AuthService.validate_session(
            db=db_session,
            token=token
        )

        assert validated_user is not None
        assert validated_user.id == test_user.id
        assert validated_user.username == test_user.username

    async def test_validate_session_invalid_token(self, db_session: AsyncSession):
        """Test session validation with invalid token"""
        user = await AuthService.validate_session(
            db=db_session,
            token="invalid-token-xyz"
        )

        assert user is None

    async def test_validate_session_expired(self, db_session: AsyncSession, test_user: User):
        """Test session validation with expired session"""
        from app.utils.security import generate_session_token

        # Create expired session
        token = generate_session_token()
        expired_session = Session(
            user_id=test_user.id,
            token=token,
            ip_address="127.0.0.1",
            expires_at=datetime.utcnow() - timedelta(minutes=1)  # Expired
        )
        db_session.add(expired_session)
        await db_session.commit()

        # Validate - should return None and delete session
        user = await AuthService.validate_session(
            db=db_session,
            token=token
        )

        assert user is None

        # Verify session was deleted
        result = await db_session.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()
        assert session is None

    async def test_logout_success(self, db_session: AsyncSession, test_user: User):
        """Test successful logout"""
        # Login first
        user, token, _ = await AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="TestPassword123!",
            ip_address="127.0.0.1"
        )

        # Logout
        result = await AuthService.logout(
            db=db_session,
            token=token
        )

        assert result is True

        # Verify session was deleted
        db_result = await db_session.execute(
            select(Session).where(Session.token == token)
        )
        session = db_result.scalar_one_or_none()
        assert session is None

    async def test_logout_invalid_token(self, db_session: AsyncSession):
        """Test logout with invalid token"""
        result = await AuthService.logout(
            db=db_session,
            token="invalid-token"
        )

        assert result is False

    async def test_change_password_success(self, db_session: AsyncSession, test_user: User):
        """Test successful password change"""
        success, message = await AuthService.change_password(
            db=db_session,
            user=test_user,
            old_password="TestPassword123!",
            new_password="NewTestPassword456!"
        )

        assert success is True
        assert "successful" in message.lower()

        # Verify password was changed
        await db_session.refresh(test_user)
        assert verify_password("NewTestPassword456!", test_user.password_hash) is True
        assert test_user.must_change_password is False

    async def test_change_password_wrong_old_password(self, db_session: AsyncSession, test_user: User):
        """Test password change with incorrect old password"""
        success, message = await AuthService.change_password(
            db=db_session,
            user=test_user,
            old_password="WrongOldPassword123!",
            new_password="NewPassword456!"
        )

        assert success is False
        assert "incorrect" in message.lower()

    async def test_change_password_weak_new_password(self, db_session: AsyncSession, test_user: User):
        """Test password change with weak new password"""
        success, message = await AuthService.change_password(
            db=db_session,
            user=test_user,
            old_password="TestPassword123!",
            new_password="weak"  # Too weak
        )

        assert success is False
        assert len(message) > 0

    async def test_cleanup_expired_sessions(self, db_session: AsyncSession, test_user: User):
        """Test cleanup of expired sessions"""
        from app.utils.security import generate_session_token

        # Create 3 expired sessions
        for i in range(3):
            token = generate_session_token()
            expired_session = Session(
                user_id=test_user.id,
                token=token,
                ip_address="127.0.0.1",
                expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            db_session.add(expired_session)

        # Create 1 valid session
        valid_token = generate_session_token()
        valid_session = Session(
            user_id=test_user.id,
            token=valid_token,
            ip_address="127.0.0.1",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(valid_session)
        await db_session.commit()

        # Run cleanup
        count = await AuthService.cleanup_expired_sessions(db_session)

        assert count == 3

        # Verify only valid session remains
        result = await db_session.execute(select(Session))
        sessions = result.scalars().all()
        assert len(sessions) == 1
        assert sessions[0].token == valid_token

    async def test_session_expiration_time(self, db_session: AsyncSession, test_user: User):
        """Test session expiration time is set correctly"""
        user, token, _ = await AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="TestPassword123!",
            ip_address="127.0.0.1"
        )

        # Get session
        result = await db_session.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one()

        # Verify expiration is approximately SESSION_EXPIRE_MINUTES from now
        expected_expiry = datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())

        # Allow 5 seconds difference for test execution time
        assert time_diff < 5

    async def test_failed_login_attempts_reset_on_success(self, db_session: AsyncSession, test_user: User):
        """Test failed login attempts are reset on successful login"""
        # Make a few failed attempts
        for i in range(3):
            await AuthService.authenticate_user(
                db=db_session,
                username="testuser",
                password="WrongPassword123!",
                ip_address="127.0.0.1"
            )

        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 3

        # Successful login
        user, token, _ = await AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="TestPassword123!",
            ip_address="127.0.0.1"
        )

        assert user.failed_login_attempts == 0
        assert user.locked_until is None
