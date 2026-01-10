"""Authentication router"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
)
from app.services.auth_service import AuthService
from app.routers.dependencies import get_current_active_user, get_client_ip
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    client_ip: str = Depends(get_client_ip),
    user_agent: Optional[str] = Header(None)
):
    """
    User login endpoint
    
    Returns a session token on successful authentication
    """
    user, token, message = await AuthService.authenticate_user(
        db=db,
        username=login_data.username,
        password=login_data.password,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    if not user or not token:
        # Log failed login attempt
        from app.services.audit_service import AuditService
        await AuditService.log_action(
            db=db,
            user_id=None,
            action="login_failed",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"username": login_data.username, "reason": message}
        )
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # Log successful login
    from app.services.audit_service import AuditService
    await AuditService.log_action(
        db=db,
        user_id=user.id,
        action="login",
        ip_address=client_ip,
        user_agent=user_agent
    )
    await db.commit()
    
    return LoginResponse(
        success=True,
        token=token,
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        must_change_password=user.must_change_password,
        message=message
    )


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    client_ip: str = Depends(get_client_ip),
    user_agent: Optional[str] = Header(None)
):
    """User logout endpoint"""
    if not authorization:
        return {"success": False, "message": "No token provided"}
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return {"success": False, "message": "Invalid token format"}
    
    token = parts[1]
    
    # Get user before logout for audit log
    from app.routers.dependencies import get_current_user
    try:
        user = await AuthService.validate_session(db, token)
        user_id = user.id if user else None
    except:
        user_id = None
    
    success = await AuthService.logout(db, token)
    
    # Log logout
    if success and user_id:
        from app.services.audit_service import AuditService
        await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="logout",
            ip_address=client_ip,
            user_agent=user_agent
        )
        await db.commit()
    
    return {
        "success": success,
        "message": "Logged out successfully" if success else "Session not found"
    }


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    success, message = await AuthService.change_password(
        db=db,
        user=current_user,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message
    }


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "must_change_password": current_user.must_change_password,
        "created_at": current_user.created_at.isoformat(),
        "updated_at": current_user.updated_at.isoformat()
    }
