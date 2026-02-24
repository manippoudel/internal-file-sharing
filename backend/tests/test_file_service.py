"""
Tests for file service

Tests cover:
- Upload initialization
- Chunk upload with checksum verification
- Complete upload and file assembly
- Cancel upload and cleanup
- List files with pagination, sorting, search
- Soft delete files
- Restore deleted files
- Rename files
- Duplicate detection
- Cleanup expired chunks
- Cleanup old deleted files
"""
import pytest
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.file_service import FileService
from app.models.file import File, SyncStatus
from app.models.sync import UploadChunk
from app.models.user import User


pytestmark = pytest.mark.asyncio


class TestFileService:
    """Test file service operations"""

    async def test_initialize_upload(self, db_session: AsyncSession, test_user: User, temp_storage_dirs: dict):
        """Test upload initialization"""
        filename = "test_document.pdf"
        file_size = 150000000  # 150 MB
        total_chunks = 3

        upload_id, chunk_size = await FileService.initialize_upload(
            db=db_session,
            filename=filename,
            file_size=file_size,
            total_chunks=total_chunks,
            user_id=test_user.id,
            mime_type="application/pdf"
        )

        assert upload_id is not None
        assert isinstance(upload_id, uuid.UUID)
        assert chunk_size > 0

    async def test_upload_chunk(self, db_session: AsyncSession, test_user: User, temp_storage_dirs: dict):
        """Test chunk upload with checksum verification"""
        # Initialize upload
        upload_id, _ = await FileService.initialize_upload(
            db=db_session,
            filename="test.pdf",
            file_size=100000,
            total_chunks=2,
            user_id=test_user.id
        )

        # Create chunk data
        chunk_data = b"This is chunk data for testing" * 1000
        checksum = hashlib.sha256(chunk_data).hexdigest()

        # Upload chunk
        result = await FileService.upload_chunk(
            db=db_session,
            upload_id=upload_id,
            chunk_number=1,
            chunk_data=chunk_data,
            filename="test.pdf",
            total_chunks=2,
            checksum=checksum
        )

        assert result is True

        # Verify chunk was saved in database
        db_result = await db_session.execute(
            select(UploadChunk).where(UploadChunk.upload_id == upload_id)
        )
        chunk_record = db_result.scalar_one_or_none()
        assert chunk_record is not None
        assert chunk_record.chunk_number == 1
        assert chunk_record.checksum == checksum

    async def test_upload_chunk_checksum_mismatch(self, db_session: AsyncSession, test_user: User):
        """Test chunk upload fails with wrong checksum"""
        upload_id, _ = await FileService.initialize_upload(
            db=db_session,
            filename="test.pdf",
            file_size=100000,
            total_chunks=2,
            user_id=test_user.id
        )

        chunk_data = b"Test chunk data"
        wrong_checksum = "wrongchecksumvalue123"

        with pytest.raises(ValueError, match="checksum mismatch"):
            await FileService.upload_chunk(
                db=db_session,
                upload_id=upload_id,
                chunk_number=1,
                chunk_data=chunk_data,
                filename="test.pdf",
                total_chunks=2,
                checksum=wrong_checksum
            )

    async def test_complete_upload(self, db_session: AsyncSession, test_user: User, temp_storage_dirs: dict):
        """Test complete upload assembles chunks correctly"""
        filename = "complete_test.txt"

        # Initialize upload
        upload_id, _ = await FileService.initialize_upload(
            db=db_session,
            filename=filename,
            file_size=60,
            total_chunks=2,
            user_id=test_user.id,
            mime_type="text/plain"
        )

        # Upload chunks
        chunk1_data = b"First chunk content"
        chunk1_checksum = hashlib.sha256(chunk1_data).hexdigest()
        await FileService.upload_chunk(
            db=db_session,
            upload_id=upload_id,
            chunk_number=0,
            chunk_data=chunk1_data,
            filename=filename,
            total_chunks=2,
            checksum=chunk1_checksum
        )

        chunk2_data = b"Second chunk content"
        chunk2_checksum = hashlib.sha256(chunk2_data).hexdigest()
        await FileService.upload_chunk(
            db=db_session,
            upload_id=upload_id,
            chunk_number=1,
            chunk_data=chunk2_data,
            filename=filename,
            total_chunks=2,
            checksum=chunk2_checksum
        )

        # Calculate final checksum
        final_data = chunk1_data + chunk2_data
        final_checksum = hashlib.sha256(final_data).hexdigest()

        # Complete upload
        file_record = await FileService.complete_upload(
            db=db_session,
            upload_id=upload_id,
            filename=filename,
            final_checksum=final_checksum,
            user_id=test_user.id,
            mime_type="text/plain"
        )

        assert file_record is not None
        assert file_record.filename == filename
        assert file_record.uploaded_by == test_user.id
        assert file_record.checksum == final_checksum
        assert file_record.is_deleted is False
        assert file_record.sync_status == SyncStatus.PENDING

        # Verify chunks were cleaned up
        result = await db_session.execute(
            select(UploadChunk).where(UploadChunk.upload_id == upload_id)
        )
        chunks = result.scalars().all()
        assert len(chunks) == 0

    async def test_cancel_upload(self, db_session: AsyncSession, test_user: User):
        """Test upload cancellation cleans up chunks"""
        upload_id, _ = await FileService.initialize_upload(
            db=db_session,
            filename="cancel_test.pdf",
            file_size=100000,
            total_chunks=3,
            user_id=test_user.id
        )

        # Upload a chunk
        chunk_data = b"Test chunk to be cancelled"
        checksum = hashlib.sha256(chunk_data).hexdigest()
        await FileService.upload_chunk(
            db=db_session,
            upload_id=upload_id,
            chunk_number=1,
            chunk_data=chunk_data,
            filename="cancel_test.pdf",
            total_chunks=3,
            checksum=checksum
        )

        # Cancel upload
        result = await FileService.cancel_upload(
            db=db_session,
            upload_id=upload_id
        )

        assert result is True

        # Verify chunks were deleted
        db_result = await db_session.execute(
            select(UploadChunk).where(UploadChunk.upload_id == upload_id)
        )
        chunks = db_result.scalars().all()
        assert len(chunks) == 0

    async def test_list_files_default(self, db_session: AsyncSession, test_file: File):
        """Test listing files with default parameters"""
        files, total = await FileService.list_files(db=db_session)

        assert total >= 1
        assert len(files) >= 1
        assert any(f.id == test_file.id for f in files)

    async def test_list_files_pagination(self, db_session: AsyncSession, test_user: User, create_test_file):
        """Test file listing pagination"""
        # Create multiple files
        for i in range(5):
            content = f"File {i} content".encode()
            file_path = create_test_file(f"file_{i}.txt", content)
            checksum = hashlib.sha256(content).hexdigest()

            file_obj = File(
                filename=f"file_{i}.txt",
                filepath=str(file_path),
                size=len(content),
                checksum=checksum,
                mime_type="text/plain",
                uploaded_by=test_user.id,
                upload_date=datetime.utcnow(),
                is_deleted=False
            )
            db_session.add(file_obj)

        await db_session.commit()

        # Test pagination
        files_page1, total = await FileService.list_files(
            db=db_session,
            page=1,
            page_size=3
        )

        assert total >= 5
        assert len(files_page1) == 3

        files_page2, _ = await FileService.list_files(
            db=db_session,
            page=2,
            page_size=3
        )

        assert len(files_page2) >= 2

    async def test_list_files_search(self, db_session: AsyncSession, test_user: User, create_test_file):
        """Test file listing with search"""
        # Create files with different names
        searchable_content = b"Searchable file"
        file_path = create_test_file("searchable_document.pdf", searchable_content)
        checksum = hashlib.sha256(searchable_content).hexdigest()

        searchable_file = File(
            filename="searchable_document.pdf",
            filepath=str(file_path),
            size=len(searchable_content),
            checksum=checksum,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            upload_date=datetime.utcnow(),
            is_deleted=False
        )
        db_session.add(searchable_file)
        await db_session.commit()

        # Search for file
        files, total = await FileService.list_files(
            db=db_session,
            search_query="searchable"
        )

        assert total >= 1
        assert any(f.filename == "searchable_document.pdf" for f in files)

    async def test_list_files_sorting(self, db_session: AsyncSession):
        """Test file listing with different sort options"""
        # Test sort by filename ascending
        files, _ = await FileService.list_files(
            db=db_session,
            sort_by="filename",
            sort_order="asc"
        )

        if len(files) >= 2:
            assert files[0].filename <= files[1].filename

        # Test sort by size descending
        files, _ = await FileService.list_files(
            db=db_session,
            sort_by="size",
            sort_order="desc"
        )

        if len(files) >= 2:
            assert files[0].size >= files[1].size

    async def test_get_file(self, db_session: AsyncSession, test_file: File):
        """Test getting file by ID"""
        file_record = await FileService.get_file(
            db=db_session,
            file_id=test_file.id
        )

        assert file_record is not None
        assert file_record.id == test_file.id
        assert file_record.filename == test_file.filename

    async def test_get_file_not_found(self, db_session: AsyncSession):
        """Test getting non-existent file"""
        file_record = await FileService.get_file(
            db=db_session,
            file_id=uuid.uuid4()
        )

        assert file_record is None

    async def test_soft_delete_file(self, db_session: AsyncSession, test_file: File, test_user: User):
        """Test soft deleting a file"""
        file_record = await FileService.soft_delete_file(
            db=db_session,
            file_id=test_file.id,
            user_id=test_user.id
        )

        assert file_record.is_deleted is True
        assert file_record.deleted_at is not None
        assert file_record.deleted_by == test_user.id

    async def test_soft_delete_already_deleted(self, db_session: AsyncSession, deleted_file: File, test_user: User):
        """Test soft deleting an already deleted file fails"""
        with pytest.raises(ValueError, match="already deleted"):
            await FileService.soft_delete_file(
                db=db_session,
                file_id=deleted_file.id,
                user_id=test_user.id
            )

    async def test_soft_delete_not_found(self, db_session: AsyncSession, test_user: User):
        """Test soft deleting non-existent file fails"""
        with pytest.raises(ValueError, match="not found"):
            await FileService.soft_delete_file(
                db=db_session,
                file_id=uuid.uuid4(),
                user_id=test_user.id
            )

    async def test_restore_file(self, db_session: AsyncSession, deleted_file: File):
        """Test restoring a deleted file"""
        file_record = await FileService.restore_file(
            db=db_session,
            file_id=deleted_file.id
        )

        assert file_record.is_deleted is False
        assert file_record.deleted_at is None
        assert file_record.deleted_by is None

    async def test_restore_active_file(self, db_session: AsyncSession, test_file: File):
        """Test restoring an active file fails"""
        with pytest.raises(ValueError, match="not deleted"):
            await FileService.restore_file(
                db=db_session,
                file_id=test_file.id
            )

    async def test_restore_file_not_found(self, db_session: AsyncSession):
        """Test restoring non-existent file fails"""
        with pytest.raises(ValueError, match="not found"):
            await FileService.restore_file(
                db=db_session,
                file_id=uuid.uuid4()
            )

    async def test_rename_file(self, db_session: AsyncSession, test_file: File):
        """Test renaming a file"""
        new_filename = "renamed_file.txt"

        file_record = await FileService.rename_file(
            db=db_session,
            file_id=test_file.id,
            new_filename=new_filename
        )

        assert file_record.filename == new_filename

    async def test_rename_file_not_found(self, db_session: AsyncSession):
        """Test renaming non-existent file fails"""
        with pytest.raises(ValueError, match="not found"):
            await FileService.rename_file(
                db=db_session,
                file_id=uuid.uuid4(),
                new_filename="new_name.txt"
            )

    async def test_check_duplicate(self, db_session: AsyncSession, test_file: File):
        """Test duplicate file detection"""
        duplicate = await FileService.check_duplicate(
            db=db_session,
            filename=test_file.filename
        )

        assert duplicate is not None
        assert duplicate.id == test_file.id

    async def test_check_duplicate_not_found(self, db_session: AsyncSession):
        """Test duplicate check for non-existent filename"""
        duplicate = await FileService.check_duplicate(
            db=db_session,
            filename="nonexistent_file.xyz"
        )

        assert duplicate is None

    async def test_check_duplicate_exclude_deleted(self, db_session: AsyncSession, deleted_file: File):
        """Test duplicate check excludes deleted files by default"""
        duplicate = await FileService.check_duplicate(
            db=db_session,
            filename=deleted_file.filename,
            include_deleted=False
        )

        assert duplicate is None

    async def test_check_duplicate_include_deleted(self, db_session: AsyncSession, deleted_file: File):
        """Test duplicate check can include deleted files"""
        duplicate = await FileService.check_duplicate(
            db=db_session,
            filename=deleted_file.filename,
            include_deleted=True
        )

        assert duplicate is not None
        assert duplicate.id == deleted_file.id

    async def test_cleanup_expired_chunks(self, db_session: AsyncSession):
        """Test cleanup of expired upload chunks"""
        # Create expired chunk
        upload_id = uuid.uuid4()
        expired_chunk = UploadChunk(
            upload_id=upload_id,
            filename="expired.pdf",
            total_chunks=2,
            chunk_number=1,
            chunk_size=1000,
            checksum="abc123",
            expires_at=datetime.utcnow() - timedelta(hours=25),  # Expired
            file_path="/tmp/chunk_1"
        )
        db_session.add(expired_chunk)

        # Create valid chunk
        valid_upload_id = uuid.uuid4()
        valid_chunk = UploadChunk(
            upload_id=valid_upload_id,
            filename="valid.pdf",
            total_chunks=2,
            chunk_number=1,
            chunk_size=1000,
            checksum="def456",
            expires_at=datetime.utcnow() + timedelta(hours=1),  # Still valid
            file_path="/tmp/chunk_2"
        )
        db_session.add(valid_chunk)
        await db_session.commit()

        # Run cleanup
        count = await FileService.cleanup_expired_chunks(db_session)

        assert count == 1

        # Verify only valid chunk remains
        result = await db_session.execute(select(UploadChunk))
        remaining_chunks = result.scalars().all()
        assert len(remaining_chunks) == 1
        assert remaining_chunks[0].upload_id == valid_upload_id

    async def test_cleanup_old_deleted_files(self, db_session: AsyncSession, test_user: User, create_test_file):
        """Test cleanup of files past retention period"""
        from app.config import settings

        # Create old deleted file
        old_content = b"Old deleted file"
        old_file_path = create_test_file("old_deleted.txt", old_content, "deleted")
        old_checksum = hashlib.sha256(old_content).hexdigest()

        old_deleted_file = File(
            filename="old_deleted.txt",
            filepath=str(old_file_path),
            size=len(old_content),
            checksum=old_checksum,
            mime_type="text/plain",
            uploaded_by=test_user.id,
            upload_date=datetime.utcnow() - timedelta(days=100),
            is_deleted=True,
            deleted_at=datetime.utcnow() - timedelta(days=100),  # Past retention
            deleted_by=test_user.id
        )
        db_session.add(old_deleted_file)

        # Create recent deleted file
        recent_content = b"Recent deleted file"
        recent_file_path = create_test_file("recent_deleted.txt", recent_content, "deleted")
        recent_checksum = hashlib.sha256(recent_content).hexdigest()

        recent_deleted_file = File(
            filename="recent_deleted.txt",
            filepath=str(recent_file_path),
            size=len(recent_content),
            checksum=recent_checksum,
            mime_type="text/plain",
            uploaded_by=test_user.id,
            upload_date=datetime.utcnow() - timedelta(days=30),
            is_deleted=True,
            deleted_at=datetime.utcnow() - timedelta(days=30),  # Within retention
            deleted_by=test_user.id
        )
        db_session.add(recent_deleted_file)
        await db_session.commit()

        # Run cleanup
        count = await FileService.cleanup_old_deleted_files(db_session)

        assert count == 1

        # Verify only recent file remains
        result = await db_session.execute(
            select(File).where(File.is_deleted == True)
        )
        remaining_files = result.scalars().all()
        assert len(remaining_files) == 1
        assert remaining_files[0].id == recent_deleted_file.id
