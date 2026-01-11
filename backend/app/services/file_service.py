"""File service for managing file uploads, downloads, and operations"""
import os
import uuid
import shutil
import zipfile
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, BinaryIO
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
import aiofiles

from app.models.file import File, SyncStatus
from app.models.sync import UploadChunk
from app.models.user import User
from app.utils.file_utils import (
    calculate_checksum,
    ensure_directory_exists,
    is_safe_path
)
from app.config import settings


class FileService:
    """Service for file management operations"""
    
    @staticmethod
    async def initialize_upload(
        db: AsyncSession,
        filename: str,
        file_size: int,
        total_chunks: int,
        user_id: uuid.UUID,
        mime_type: Optional[str] = None
    ) -> Tuple[uuid.UUID, int]:
        """
        Initialize a chunked file upload
        
        Returns:
            Tuple of (upload_id, chunk_size)
        """
        upload_id = uuid.uuid4()
        chunk_size = settings.CHUNK_SIZE
        
        # Create upload directory
        upload_dir = os.path.join(settings.TEMP_FILES_PATH, str(upload_id))
        await ensure_directory_exists(upload_dir)
        
        # Store upload metadata in chunks table
        # Chunks will be added as they are uploaded
        
        return upload_id, chunk_size
    
    @staticmethod
    async def upload_chunk(
        db: AsyncSession,
        upload_id: uuid.UUID,
        chunk_number: int,
        chunk_data: bytes,
        filename: str,
        total_chunks: int,
        checksum: str
    ) -> bool:
        """
        Upload a file chunk
        
        Returns:
            True if successful
        """
        # Verify checksum
        import hashlib
        actual_checksum = hashlib.sha256(chunk_data).hexdigest()
        if actual_checksum != checksum:
            raise ValueError("Chunk checksum mismatch")
        
        # Save chunk to temp directory
        upload_dir = os.path.join(settings.TEMP_FILES_PATH, str(upload_id))
        chunk_path = os.path.join(upload_dir, f"chunk_{chunk_number}")
        
        async with aiofiles.open(chunk_path, 'wb') as f:
            await f.write(chunk_data)
        
        # Store chunk metadata
        expires_at = datetime.utcnow() + timedelta(hours=24)
        chunk_record = UploadChunk(
            upload_id=upload_id,
            filename=filename,
            total_chunks=total_chunks,
            chunk_number=chunk_number,
            chunk_size=len(chunk_data),
            checksum=checksum,
            expires_at=expires_at,
            file_path=chunk_path
        )
        
        db.add(chunk_record)
        await db.commit()
        
        return True
    
    @staticmethod
    async def complete_upload(
        db: AsyncSession,
        upload_id: uuid.UUID,
        filename: str,
        final_checksum: str,
        user_id: uuid.UUID,
        mime_type: Optional[str] = None
    ) -> File:
        """
        Complete a chunked upload by assembling chunks into final file
        
        Returns:
            File record
        """
        # Get all chunks for this upload
        result = await db.execute(
            select(UploadChunk)
            .where(UploadChunk.upload_id == upload_id)
            .order_by(UploadChunk.chunk_number)
        )
        chunks = result.scalars().all()
        
        if not chunks:
            raise ValueError("No chunks found for this upload")
        
        # Verify all chunks are present
        expected_chunks = chunks[0].total_chunks
        if len(chunks) != expected_chunks:
            raise ValueError(f"Expected {expected_chunks} chunks, found {len(chunks)}")
        
        # Create final file directory
        now = datetime.utcnow()
        year_month = now.strftime("%Y/%m")
        final_dir = os.path.join(settings.ACTIVE_FILES_PATH, year_month)
        await ensure_directory_exists(final_dir)
        
        # Generate unique filename on disk
        file_id = uuid.uuid4()
        file_ext = os.path.splitext(filename)[1]
        disk_filename = f"{file_id}{file_ext}"
        final_path = os.path.join(final_dir, disk_filename)
        
        # Assemble chunks into final file
        async with aiofiles.open(final_path, 'wb') as final_file:
            for chunk in chunks:
                async with aiofiles.open(chunk.file_path, 'rb') as chunk_file:
                    chunk_data = await chunk_file.read()
                    await final_file.write(chunk_data)
        
        # Verify final checksum
        actual_checksum = await calculate_checksum(final_path)
        if actual_checksum != final_checksum:
            # Delete assembled file
            os.remove(final_path)
            raise ValueError("Final file checksum mismatch")
        
        # Get file size
        file_size = os.path.getsize(final_path)
        
        # Create file record
        file_record = File(
            id=file_id,
            filename=filename,
            filepath=final_path,
            size=file_size,
            checksum=final_checksum,
            mime_type=mime_type,
            uploaded_by=user_id,
            upload_date=now,
            is_deleted=False,
            sync_status=SyncStatus.PENDING
        )
        
        db.add(file_record)
        
        # Clean up chunks
        upload_dir = os.path.join(settings.TEMP_FILES_PATH, str(upload_id))
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        
        # Delete chunk records
        for chunk in chunks:
            await db.delete(chunk)
        
        await db.commit()
        await db.refresh(file_record)
        
        return file_record
    
    @staticmethod
    async def cancel_upload(
        db: AsyncSession,
        upload_id: uuid.UUID
    ) -> bool:
        """Cancel an upload and clean up chunks"""
        # Get chunks
        result = await db.execute(
            select(UploadChunk).where(UploadChunk.upload_id == upload_id)
        )
        chunks = result.scalars().all()
        
        # Delete chunk records
        for chunk in chunks:
            await db.delete(chunk)
        
        # Clean up temp directory
        upload_dir = os.path.join(settings.TEMP_FILES_PATH, str(upload_id))
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        
        await db.commit()
        return True
    
    @staticmethod
    async def list_files(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 100,
        sort_by: str = "upload_date",
        sort_order: str = "desc",
        search_query: Optional[str] = None,
        include_deleted: bool = False
    ) -> Tuple[List[File], int]:
        """
        List files with pagination and sorting
        
        Returns:
            Tuple of (files, total_count)
        """
        # Build query
        query = select(File)
        
        # Filter deleted files
        if not include_deleted:
            query = query.where(File.is_deleted == False)
        
        # Search filter
        if search_query:
            query = query.where(File.filename.ilike(f"%{search_query}%"))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()
        
        # Apply sorting
        if sort_by == "filename":
            sort_col = File.filename
        elif sort_by == "size":
            sort_col = File.size
        elif sort_by == "upload_date":
            sort_col = File.upload_date
        else:
            sort_col = File.upload_date
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(sort_col)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        files = result.scalars().all()
        
        return files, total
    
    @staticmethod
    async def get_file(
        db: AsyncSession,
        file_id: uuid.UUID
    ) -> Optional[File]:
        """Get file by ID"""
        result = await db.execute(
            select(File).where(File.id == file_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def soft_delete_file(
        db: AsyncSession,
        file_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> File:
        """Soft delete a file"""
        file_record = await FileService.get_file(db, file_id)
        if not file_record:
            raise ValueError("File not found")
        
        if file_record.is_deleted:
            raise ValueError("File already deleted")
        
        # Move file to deleted directory
        now = datetime.utcnow()
        year_month = now.strftime("%Y/%m")
        deleted_dir = os.path.join(settings.DELETED_FILES_PATH, year_month)
        await ensure_directory_exists(deleted_dir)
        
        # Get filename from path
        filename_on_disk = os.path.basename(file_record.filepath)
        new_path = os.path.join(deleted_dir, filename_on_disk)
        
        # Move file
        if os.path.exists(file_record.filepath):
            shutil.move(file_record.filepath, new_path)
        
        # Update record
        file_record.is_deleted = True
        file_record.deleted_at = now
        file_record.deleted_by = user_id
        file_record.filepath = new_path
        
        await db.commit()
        await db.refresh(file_record)
        
        return file_record
    
    @staticmethod
    async def restore_file(
        db: AsyncSession,
        file_id: uuid.UUID
    ) -> File:
        """Restore a soft-deleted file"""
        file_record = await FileService.get_file(db, file_id)
        if not file_record:
            raise ValueError("File not found")
        
        if not file_record.is_deleted:
            raise ValueError("File is not deleted")
        
        # Move file back to active directory
        now = datetime.utcnow()
        year_month = now.strftime("%Y/%m")
        active_dir = os.path.join(settings.ACTIVE_FILES_PATH, year_month)
        await ensure_directory_exists(active_dir)
        
        # Get filename from path
        filename_on_disk = os.path.basename(file_record.filepath)
        new_path = os.path.join(active_dir, filename_on_disk)
        
        # Move file
        if os.path.exists(file_record.filepath):
            shutil.move(file_record.filepath, new_path)
        
        # Update record
        file_record.is_deleted = False
        file_record.deleted_at = None
        file_record.deleted_by = None
        file_record.filepath = new_path
        
        await db.commit()
        await db.refresh(file_record)
        
        return file_record
    
    @staticmethod
    async def rename_file(
        db: AsyncSession,
        file_id: uuid.UUID,
        new_filename: str
    ) -> File:
        """Rename a file"""
        file_record = await FileService.get_file(db, file_id)
        if not file_record:
            raise ValueError("File not found")
        
        # Update filename
        file_record.filename = new_filename
        
        await db.commit()
        await db.refresh(file_record)
        
        return file_record
    
    @staticmethod
    async def check_duplicate(
        db: AsyncSession,
        filename: str,
        include_deleted: bool = False
    ) -> Optional[File]:
        """Check if a file with the same name exists"""
        query = select(File).where(File.filename == filename)
        
        if not include_deleted:
            query = query.where(File.is_deleted == False)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def cleanup_expired_chunks(db: AsyncSession) -> int:
        """Clean up expired upload chunks"""
        result = await db.execute(
            select(UploadChunk).where(UploadChunk.expires_at < datetime.utcnow())
        )
        expired_chunks = result.scalars().all()
        
        count = 0
        upload_ids_to_clean = set()
        
        for chunk in expired_chunks:
            upload_ids_to_clean.add(chunk.upload_id)
            await db.delete(chunk)
            count += 1
        
        # Clean up temp directories
        for upload_id in upload_ids_to_clean:
            upload_dir = os.path.join(settings.TEMP_FILES_PATH, str(upload_id))
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)
        
        await db.commit()
        
        return count
    
    @staticmethod
    async def cleanup_old_deleted_files(db: AsyncSession) -> int:
        """Permanently delete files past retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.DELETED_FILES_RETENTION_DAYS)
        
        result = await db.execute(
            select(File).where(
                and_(
                    File.is_deleted == True,
                    File.deleted_at < cutoff_date
                )
            )
        )
        old_files = result.scalars().all()
        
        count = 0
        for file_record in old_files:
            # Delete physical file
            if os.path.exists(file_record.filepath):
                os.remove(file_record.filepath)
            
            # Delete record
            await db.delete(file_record)
            count += 1
        
        await db.commit()
        
        return count
