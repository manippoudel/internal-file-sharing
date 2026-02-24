"""
Tests for admin functionality through API endpoints

Tests cover:
- Admin can list all users
- Admin can create users
- Admin can update user roles
- Admin can delete users
- Admin can unlock accounts
- Admin can reset passwords
- Regular users cannot access admin endpoints
- System health and storage metrics
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


pytestmark = pytest.mark.asyncio


class TestAdminEndpoints:
    """Test admin-only endpoints"""

    async def test_admin_list_users(self, client: AsyncClient, admin_headers: dict, test_user: User):
        """Test admin can list all users"""
        response = await client.get(
            "/api/v1/admin/users",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_admin_create_user(self, client: AsyncClient, admin_headers: dict):
        """Test admin can create new users"""
        response = await client.post(
            "/api/v1/admin/users",
            headers=admin_headers,
            json={
                "username": "newadminuser",
                "email": "newadminuser@example.com",
                "password": "NewAdminUser123!",
                "role": "user"
            }
        )

        assert response.status_code == 200 or response.status_code == 201
        data = response.json()
        assert data["username"] == "newadminuser"

    async def test_admin_update_user_role(self, client: AsyncClient, admin_headers: dict, test_user: User):
        """Test admin can update user roles"""
        response = await client.put(
            f"/api/v1/admin/users/{test_user.id}",
            headers=admin_headers,
            json={
                "role": "admin",
                "is_active": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    async def test_admin_delete_user(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test admin can delete users"""
        from app.services.auth_service import AuthService

        # Create user to delete
        temp_user = await AuthService.create_user(
            db=db_session,
            username="tempdeleteuser",
            email="tempdelete@example.com",
            password="TempDelete123!",
            role=UserRole.user
        )

        response = await client.delete(
            f"/api/v1/admin/users/{temp_user.id}",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_admin_unlock_account(self, client: AsyncClient, admin_headers: dict, locked_user: User):
        """Test admin can unlock locked accounts"""
        response = await client.post(
            f"/api/v1/admin/users/{locked_user.id}/unlock",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_admin_reset_password(self, client: AsyncClient, admin_headers: dict, test_user: User):
        """Test admin can reset user passwords"""
        response = await client.post(
            f"/api/v1/admin/users/{test_user.id}/reset-password",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "new_password" in data or "password" in data

    async def test_regular_user_cannot_access_admin(self, client: AsyncClient, auth_headers: dict):
        """Test regular users cannot access admin endpoints"""
        response = await client.get(
            "/api/v1/admin/users",
            headers=auth_headers
        )

        assert response.status_code == 403

    async def test_admin_dashboard_stats(self, client: AsyncClient, admin_headers: dict):
        """Test admin dashboard statistics"""
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data or "users" in data
        assert "total_files" in data or "files" in data

    async def test_admin_storage_metrics(self, client: AsyncClient, admin_headers: dict):
        """Test storage metrics endpoint"""
        response = await client.get(
            "/api/v1/admin/storage",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_storage" in data or "storage" in data or "used" in data

    async def test_admin_system_health(self, client: AsyncClient, admin_headers: dict):
        """Test system health metrics"""
        response = await client.get(
            "/api/v1/admin/health",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data or "memory" in data or "status" in data
