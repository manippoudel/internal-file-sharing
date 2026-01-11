"""Authentication service"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.session import Session
from app.utils.security import (
    hash_password,
    verify_password,
    generate_session_token,
    validate_password_strength
)
from app.config import settings


class AuthService:
    """Authentication service for user login, logout, and session management"""
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        password: str,
        email: str,
        role: UserRole = UserRole.USER
    ) -> User:
        """Create a new user"""
        password_hash = hash_password(password)
        
        user = User(
            username=username,
            password_hash=password_hash,
            email=email,
            role=role,
            is_active=True,
            must_change_password=True
        )
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[User], Optional[str], str]:
        """
        Authenticate a user
        
        Returns:
            Tuple of (User, session_token, message)
        """
        # Get user by username
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None, None, "Invalid username or password"
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            return None, None, f"Account is locked. Try again in {remaining} minutes"
        
        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )
                await db.commit()
                return None, None, f"Account locked due to too many failed login attempts"
            
            await db.commit()
            return None, None, "Invalid username or password"
        
        # Check if user is active
        if not user.is_active:
            return None, None, "Account is deactivated"
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Create session
        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
        
        session = Session(
            user_id=user.id,
            token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(user)
        
        return user, session_token, "Login successful"
    
    @staticmethod
    async def validate_session(
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """Validate a session token and return the user"""
        result = await db.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Check if session is expired
        if session.expires_at < datetime.utcnow():
            await db.delete(session)
            await db.commit()
            return None
        
        # Get user
        result = await db.execute(
            select(User).where(User.id == session.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def logout(
        db: AsyncSession,
        token: str
    ) -> bool:
        """Logout a user by invalidating their session"""
        result = await db.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()
        
        if session:
            await db.delete(session)
            await db.commit()
            return True
        
        return False
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """Change user password"""
        # Verify old password
        if not verify_password(old_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Validate new password strength
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            return False, error_msg
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        return True, "Password changed successfully"
    
    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions"""
        result = await db.execute(
            select(Session).where(Session.expires_at < datetime.utcnow())
        )
        expired_sessions = result.scalars().all()
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            await db.delete(session)
        
        await db.commit()
        
        return count
