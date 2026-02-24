#!/usr/bin/env python3
"""Script to create the admin user"""
import asyncio
import sys
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password


async def create_admin():
    """Create admin user if it doesn't exist"""
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.username == 'admin'))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print('✓ Admin user already exists')
            print('Username: admin')
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=UserRole.admin.value,  # Use .value to get the string "admin"
            is_active=True,
            must_change_password=True
        )
        db.add(admin)
        await db.commit()
        
        print('✓ Admin user created successfully!')
        print('━' * 50)
        print('Username: admin')
        print(f'Email: {settings.ADMIN_EMAIL}')
        print('Password: (from ADMIN_PASSWORD env variable)')
        print('━' * 50)
        print('⚠️  Please change the password after first login!')


if __name__ == '__main__':
    try:
        asyncio.run(create_admin())
    except Exception as e:
        print(f'❌ Error creating admin user: {e}', file=sys.stderr)
        sys.exit(1)
