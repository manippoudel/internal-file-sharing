"""
Shared pytest fixtures for all tests
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from faker import Faker

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import Base, get_db
from app.config import Settings
from app.main import app
from app.models.user import User, UserRole
from app.models.file import File
from app.services.auth_service import AuthService
from app.utils.security import hash_password


# Initialize Faker for test data generation
fake = Faker()


# Test settings override
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing"""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/filedb_test",
        DEBUG=True,
        SYNC_ENABLED=False,
        SCHEDULER_ENABLED=False,
        STORAGE_PATH="/tmp/test_data",
        ACTIVE_FILES_PATH="/tmp/test_data/active",
        DELETED_FILES_PATH="/tmp/test_data/deleted",
        TEMP_FILES_PATH="/tmp/test_data/temp",
        BACKUP_PATH="/tmp/test_data/backups",
        LOGS_PATH="/tmp/test_data/logs",
    )


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test database engine
@pytest.fixture(scope="session")
async def test_engine(test_settings):
    """Create test database engine"""
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# Session factory for tests
@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create session factory for tests"""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


# Database session per test
@pytest.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Provide clean database session for each test"""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override app dependency
@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client with overridden database dependency"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# Temporary directories for file operations
@pytest.fixture
def temp_storage_dirs(tmp_path) -> dict:
    """Create temporary directories for file storage"""
    storage_dirs = {
        "active": tmp_path / "active",
        "deleted": tmp_path / "deleted",
        "temp": tmp_path / "temp",
        "backups": tmp_path / "backups",
        "logs": tmp_path / "logs",
    }

    for directory in storage_dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    return storage_dirs


# Test user fixtures
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a regular test user"""
    user = User(
        username="testuser",
        email="testuser@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.user,
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin test user"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("AdminPassword123!"),
        role=UserRole.admin,
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def locked_user(db_session: AsyncSession) -> User:
    """Create a locked test user"""
    from datetime import datetime, timedelta

    user = User(
        username="lockeduser",
        email="locked@example.com",
        password_hash=hash_password("LockedPassword123!"),
        role=UserRole.user,
        is_active=True,
        must_change_password=False,
        failed_login_attempts=5,
        locked_until=datetime.utcnow() + timedelta(minutes=30),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# Authentication fixtures
@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for regular user"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123!",
        }
    )
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, admin_user: User) -> dict:
    """Get authentication headers for admin user"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "AdminPassword123!",
        }
    )
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# File fixtures
@pytest.fixture
async def test_file(db_session: AsyncSession, test_user: User, temp_storage_dirs: dict) -> File:
    """Create a test file in database"""
    import hashlib
    from datetime import datetime

    # Create actual file
    file_path = temp_storage_dirs["active"] / "test_file.txt"
    file_content = b"This is a test file content"
    file_path.write_bytes(file_content)

    # Calculate checksum
    checksum = hashlib.sha256(file_content).hexdigest()

    file_obj = File(
        filename="test_file.txt",
        filepath=str(file_path),
        size=len(file_content),
        checksum=checksum,
        mime_type="text/plain",
        uploaded_by=test_user.id,
        upload_date=datetime.utcnow(),
        is_deleted=False,
    )
    db_session.add(file_obj)
    await db_session.commit()
    await db_session.refresh(file_obj)
    return file_obj


@pytest.fixture
async def deleted_file(db_session: AsyncSession, test_user: User, temp_storage_dirs: dict) -> File:
    """Create a deleted test file"""
    import hashlib
    from datetime import datetime

    # Create actual file in deleted directory
    file_path = temp_storage_dirs["deleted"] / "deleted_file.txt"
    file_content = b"This is a deleted test file"
    file_path.write_bytes(file_content)

    checksum = hashlib.sha256(file_content).hexdigest()

    file_obj = File(
        filename="deleted_file.txt",
        filepath=str(file_path),
        size=len(file_content),
        checksum=checksum,
        mime_type="text/plain",
        uploaded_by=test_user.id,
        upload_date=datetime.utcnow(),
        is_deleted=True,
        deleted_at=datetime.utcnow(),
        deleted_by=test_user.id,
    )
    db_session.add(file_obj)
    await db_session.commit()
    await db_session.refresh(file_obj)
    return file_obj


# Helper fixtures
@pytest.fixture
def sample_upload_data() -> dict:
    """Sample data for file upload"""
    return {
        "filename": "sample.pdf",
        "total_chunks": 3,
        "file_size": 150000000,  # 150 MB
        "mime_type": "application/pdf",
    }


@pytest.fixture
def create_test_file(temp_storage_dirs):
    """Factory fixture to create test files"""
    def _create_file(filename: str, content: bytes, directory: str = "active") -> Path:
        file_path = temp_storage_dirs[directory] / filename
        file_path.write_bytes(content)
        return file_path
    return _create_file


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup_after_test(db_session: AsyncSession):
    """Cleanup database after each test"""
    yield
    # Test runs here
    # Cleanup happens after test
    try:
        await db_session.rollback()
    except:
        pass
