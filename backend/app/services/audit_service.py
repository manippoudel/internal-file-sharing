"""Audit logging service"""
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.user import User


class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: Optional[uuid.UUID],
        action: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        target_file_id: Optional[uuid.UUID] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Log a user action
        
        Args:
            db: Database session
            user_id: ID of user performing action (None for anonymous actions)
            action: Action type (login, logout, upload, download, delete, etc.)
            ip_address: IP address of user
            user_agent: User agent string
            target_file_id: ID of file being acted upon (if applicable)
            details: Additional details as JSON
            
        Returns:
            Created audit log record
        """
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_file_id=target_file_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        
        db.add(log_entry)
        await db.flush()
        await db.refresh(log_entry)
        
        return log_entry
    
    @staticmethod
    async def get_logs(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[AuditLog], int]:
        """
        Query audit logs with filters
        
        Returns:
            Tuple of (logs, total_count)
        """
        query = select(AuditLog)
        
        # Apply filters
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        
        if action:
            conditions.append(AuditLog.action == action)
        
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()
        
        # Apply sorting and pagination
        query = query.order_by(desc(AuditLog.timestamp))
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return logs, total
    
    @staticmethod
    async def get_activity_summary(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get activity summary report
        
        Returns:
            Dictionary with activity statistics
        """
        query = select(AuditLog)
        
        # Apply date filters
        conditions = []
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get all logs
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Calculate statistics
        total_actions = len(logs)
        
        # Count by action type
        action_counts = {}
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        # Count unique users
        unique_users = len(set(log.user_id for log in logs if log.user_id))
        
        # Most active users
        user_activity = {}
        for log in logs:
            if log.user_id:
                user_activity[str(log.user_id)] = user_activity.get(str(log.user_id), 0) + 1
        
        most_active_users = sorted(
            user_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_actions": total_actions,
            "unique_users": unique_users,
            "action_breakdown": action_counts,
            "most_active_users": [
                {"user_id": user_id, "action_count": count}
                for user_id, count in most_active_users
            ]
        }
    
    @staticmethod
    async def export_logs_csv(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs as CSV
        
        Returns:
            CSV string
        """
        import csv
        import io
        
        # Get logs
        logs, _ = await AuditService.get_logs(
            db=db,
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=100000  # Get all matching logs
        )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Timestamp',
            'User ID',
            'Action',
            'Target File ID',
            'IP Address',
            'User Agent',
            'Details'
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat(),
                str(log.user_id) if log.user_id else '',
                log.action,
                str(log.target_file_id) if log.target_file_id else '',
                log.ip_address,
                log.user_agent or '',
                str(log.details) if log.details else ''
            ])
        
        return output.getvalue()
