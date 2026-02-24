"""
Integration tests for complete workflows

Tests cover:
- Complete file upload flow: login → upload → download
- User lifecycle: create → login → change password → delete
- File lifecycle: upload → list → rename → delete → restore
- Admin workflow: create user → assign role → manage files
"""
import pytest
import hashlib
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


pytestmark = pytest.mark.asyncio


class TestIntegrationFlows:
    """Test complete user workflows"""

    async def test_complete_file_upload_download_flow(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test complete file upload and download flow"""
        # 1. Login (already done via auth_headers fixture)

        # 2. Initialize upload
        response = await client.post(
            "/api/v1/files/upload/init",
            headers=auth_headers,
            json={
                "filename": "integration_test.txt",
                "file_size": 1000,
                "total_chunks": 1,
                "mime_type": "text/plain"
            }
        )

        assert response.status_code == 200
        upload_data = response.json()
        upload_id = upload_data["upload_id"]

        # 3. Upload chunk
        chunk_data = b"Integration test file content"
        checksum = hashlib.sha256(chunk_data).hexdigest()

        response = await client.post(
            "/api/v1/files/upload/chunk",
            headers=auth_headers,
            json={
                "upload_id": upload_id,
                "chunk_number": 0,
                "filename": "integration_test.txt",
                "total_chunks": 1,
                "checksum": checksum
            },
            files={"file": chunk_data}
        )

        # May be 200 or implementation-specific
        assert response.status_code in [200, 201]

        # 4. Complete upload
        final_checksum = hashlib.sha256(chunk_data).hexdigest()

        response = await client.post(
            "/api/v1/files/upload/complete",
            headers=auth_headers,
            json={
                "upload_id": upload_id,
                "filename": "integration_test.txt",
                "checksum": final_checksum,
                "mime_type": "text/plain"
            }
        )

        assert response.status_code in [200, 201]
        file_data = response.json()
        file_id = file_data["id"]

        # 5. List files and verify
        response = await client.get(
            "/api/v1/files/browse",
            headers=auth_headers
        )

        assert response.status_code == 200
        files_data = response.json()
        assert any(f["id"] == file_id for f in files_data["files"])

        # 6. Download file
        response = await client.get(
            f"/api/v1/files/{file_id}/download",
            headers=auth_headers
        )

        assert response.status_code == 200

    async def test_user_lifecycle(
        self,
        client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession
    ):
        """Test complete user lifecycle"""
        # 1. Admin creates user
        response = await client.post(
            "/api/v1/admin/users",
            headers=admin_headers,
            json={
                "username": "lifecycleuser",
                "email": "lifecycle@example.com",
                "password": "LifeCycle123!",
                "role": "user"
            }
        )

        assert response.status_code in [200, 201]
        user_data = response.json()
        user_id = user_data["id"]

        # 2. User logs in
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "lifecycleuser",
                "password": "LifeCycle123!"
            }
        )

        assert response.status_code == 200
        login_data = response.json()
        user_token = login_data["token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 3. User changes password
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=user_headers,
            json={
                "old_password": "LifeCycle123!",
                "new_password": "NewLifeCycle456!"
            }
        )

        assert response.status_code == 200

        # 4. User logs out
        response = await client.post(
            "/api/v1/auth/logout",
            headers=user_headers
        )

        assert response.status_code == 200

        # 5. Admin deletes user
        response = await client.delete(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_file_lifecycle(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_file: dict
    ):
        """Test complete file lifecycle"""
        file_id = test_file.id

        # 1. List files
        response = await client.get(
            "/api/v1/files/browse",
            headers=auth_headers
        )

        assert response.status_code == 200

        # 2. Rename file
        response = await client.post(
            f"/api/v1/files/{file_id}/rename",
            headers=auth_headers,
            json={"new_filename": "renamed_test.txt"}
        )

        assert response.status_code == 200

        # 3. Soft delete file
        response = await client.post(
            f"/api/v1/files/{file_id}/delete",
            headers=auth_headers
        )

        assert response.status_code == 200

        # 4. List deleted files
        response = await client.get(
            "/api/v1/files/trash",
            headers=auth_headers
        )

        assert response.status_code == 200
        trash_data = response.json()
        assert any(f["id"] == file_id for f in trash_data["files"])

        # 5. Restore file
        response = await client.post(
            f"/api/v1/files/{file_id}/restore",
            headers=auth_headers
        )

        assert response.status_code == 200

        # 6. Verify file is active again
        response = await client.get(
            "/api/v1/files/browse",
            headers=auth_headers
        )

        assert response.status_code == 200
        files_data = response.json()
        assert any(f["id"] == file_id for f in files_data["files"])

    async def test_admin_workflow(
        self,
        client: AsyncClient,
        admin_headers: dict
    ):
        """Test admin managing users and files"""
        # 1. View dashboard
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers=admin_headers
        )

        assert response.status_code == 200

        # 2. Create new user
        response = await client.post(
            "/api/v1/admin/users",
            headers=admin_headers,
            json={
                "username": "adminmanageduser",
                "email": "adminmanaged@example.com",
                "password": "AdminManaged123!",
                "role": "user"
            }
        )

        assert response.status_code in [200, 201]
        user_data = response.json()
        user_id = user_data["id"]

        # 3. Update user role to admin
        response = await client.put(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers,
            json={
                "role": "admin",
                "is_active": True
            }
        )

        assert response.status_code == 200

        # 4. Check system health
        response = await client.get(
            "/api/v1/admin/health",
            headers=admin_headers
        )

        assert response.status_code == 200

        # 5. Check storage metrics
        response = await client.get(
            "/api/v1/admin/storage",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_unauthorized_access_denied(self, client: AsyncClient):
        """Test that unauthorized access is denied"""
        # Try to access protected endpoint without auth
        response = await client.get("/api/v1/files/browse")

        assert response.status_code == 401

    async def test_regular_user_cannot_access_admin_endpoints(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test regular user cannot access admin functions"""
        response = await client.get(
            "/api/v1/admin/users",
            headers=auth_headers
        )

        assert response.status_code == 403
