"""Admin router for user management and dashboard"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
import uuid
from datetime import datetime, timedelta
import psutil
import shutil

from app.database import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse
)
from app.services.auth_service import AuthService
from app.routers.dependencies import get_current_admin_user
from app.models.user import User, UserRole
from app.models.file import File
from app.models.session import Session
from app.config import settings

router = APIRouter()


# User Management Endpoints

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    # Count total users
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar()
    
    # Get users with pagination
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create user
    new_user = await AuthService.create_user(
        db=db,
        username=user_data.username,
        password=user_data.password,
        email=user_data.email,
        role=UserRole(user_data.role)
    )
    
    return UserResponse.model_validate(new_user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user details (admin only)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.role is not None:
        user.role = UserRole(user_data.role)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user sessions
    await db.execute(
        select(Session).where(Session.user_id == user_id)
    )
    sessions = result.scalars().all()
    for session in sessions:
        await db.delete(session)
    
    # Delete user
    await db.delete(user)
    await db.commit()
    
    return {
        "success": True,
        "message": f"User '{user.username}' deleted successfully"
    }


@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlock a locked user account (admin only)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.failed_login_attempts = 0
    user.locked_until = None
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"User '{user.username}' unlocked successfully"
    }


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: uuid.UUID,
    new_password: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset user password (admin only)"""
    from app.utils.security import hash_password, validate_password_strength
    
    # Validate password
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.password_hash = hash_password(new_password)
    user.must_change_password = True
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Password reset for user '{user.username}'"
    }


# Dashboard Endpoints

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics (admin only)"""
    # Count active users
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar()
    
    # Count active sessions
    active_sessions_result = await db.execute(
        select(func.count(Session.id)).where(Session.expires_at > datetime.utcnow())
    )
    active_sessions = active_sessions_result.scalar()
    
    # Count total files
    total_files_result = await db.execute(
        select(func.count(File.id)).where(File.is_deleted == False)
    )
    total_files = total_files_result.scalar()
    
    # Count deleted files
    deleted_files_result = await db.execute(
        select(func.count(File.id)).where(File.is_deleted == True)
    )
    deleted_files = deleted_files_result.scalar()
    
    # Calculate storage usage
    active_files_size_result = await db.execute(
        select(func.sum(File.size)).where(File.is_deleted == False)
    )
    active_files_size = active_files_size_result.scalar() or 0
    
    deleted_files_size_result = await db.execute(
        select(func.sum(File.size)).where(File.is_deleted == True)
    )
    deleted_files_size = deleted_files_size_result.scalar() or 0
    
    return {
        "users": {
            "total": active_users,
            "active_sessions": active_sessions,
            "max_concurrent": settings.MAX_CONCURRENT_USERS
        },
        "files": {
            "active": total_files,
            "deleted": deleted_files,
            "total": total_files + deleted_files
        },
        "storage": {
            "active_bytes": active_files_size,
            "deleted_bytes": deleted_files_size,
            "total_bytes": active_files_size + deleted_files_size,
            "active_gb": round(active_files_size / (1024**3), 2),
            "deleted_gb": round(deleted_files_size / (1024**3), 2),
            "total_gb": round((active_files_size + deleted_files_size) / (1024**3), 2)
        }
    }


@router.get("/storage")
async def get_storage_info(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed storage information (admin only)"""
    # Get disk usage
    import os
    
    storage_path = settings.STORAGE_PATH
    if os.path.exists(storage_path):
        disk_usage = shutil.disk_usage(storage_path)
        total_disk = disk_usage.total
        used_disk = disk_usage.used
        free_disk = disk_usage.free
        percent_used = (used_disk / total_disk) * 100 if total_disk > 0 else 0
    else:
        total_disk = used_disk = free_disk = 0
        percent_used = 0
    
    # Get file storage breakdown
    active_files_size_result = await db.execute(
        select(func.sum(File.size)).where(File.is_deleted == False)
    )
    active_files_size = active_files_size_result.scalar() or 0
    
    deleted_files_size_result = await db.execute(
        select(func.sum(File.size)).where(File.is_deleted == True)
    )
    deleted_files_size = deleted_files_size_result.scalar() or 0
    
    return {
        "disk": {
            "total_bytes": total_disk,
            "used_bytes": used_disk,
            "free_bytes": free_disk,
            "percent_used": round(percent_used, 2),
            "total_gb": round(total_disk / (1024**3), 2),
            "used_gb": round(used_disk / (1024**3), 2),
            "free_gb": round(free_disk / (1024**3), 2),
            "alert": percent_used > 80
        },
        "files": {
            "active_bytes": active_files_size,
            "deleted_bytes": deleted_files_size,
            "active_gb": round(active_files_size / (1024**3), 2),
            "deleted_gb": round(deleted_files_size / (1024**3), 2)
        }
    }


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system health metrics (admin only)"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_total = memory.total
    memory_used = memory.used
    memory_percent = memory.percent
    
    # Disk I/O
    disk_io = psutil.disk_io_counters()
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "count": cpu_count
        },
        "memory": {
            "total_bytes": memory_total,
            "used_bytes": memory_used,
            "percent": memory_percent,
            "total_gb": round(memory_total / (1024**3), 2),
            "used_gb": round(memory_used / (1024**3), 2)
        },
        "disk_io": {
            "read_bytes": disk_io.read_bytes if disk_io else 0,
            "write_bytes": disk_io.write_bytes if disk_io else 0,
            "read_count": disk_io.read_count if disk_io else 0,
            "write_count": disk_io.write_count if disk_io else 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system settings (admin only)"""
    return {
        "file_upload": {
            "max_upload_size_bytes": settings.MAX_UPLOAD_SIZE,
            "max_upload_size_gb": settings.MAX_UPLOAD_SIZE / (1024**3),
            "chunk_size_bytes": settings.CHUNK_SIZE,
            "chunk_size_mb": settings.CHUNK_SIZE / (1024**2),
            "max_concurrent_uploads": settings.MAX_CONCURRENT_UPLOADS,
            "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS
        },
        "authentication": {
            "session_expire_minutes": settings.SESSION_EXPIRE_MINUTES,
            "password_min_length": settings.PASSWORD_MIN_LENGTH,
            "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
            "account_lockout_minutes": settings.ACCOUNT_LOCKOUT_MINUTES,
            "max_concurrent_users": settings.MAX_CONCURRENT_USERS
        },
        "file_retention": {
            "deleted_files_retention_days": settings.DELETED_FILES_RETENTION_DAYS
        },
        "sync": {
            "sync_enabled": settings.SYNC_ENABLED
        },
        "scheduler": {
            "scheduler_enabled": settings.SCHEDULER_ENABLED
        }
    }
