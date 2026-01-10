"""File management router"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os
import zipfile
import io
import uuid

from app.database import get_db
from app.schemas.file import (
    FileUploadInit,
    FileUploadInitResponse,
    FileUploadChunk,
    FileUploadComplete,
    FileResponse,
    FileListResponse,
    FileRenameRequest,
    BulkDownloadRequest
)
from app.services.file_service import FileService
from app.routers.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/upload/init", response_model=FileUploadInitResponse)
async def initialize_upload(
    upload_data: FileUploadInit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize a chunked file upload"""
    upload_id, chunk_size = await FileService.initialize_upload(
        db=db,
        filename=upload_data.filename,
        file_size=upload_data.file_size,
        total_chunks=upload_data.total_chunks,
        user_id=current_user.id,
        mime_type=upload_data.mime_type
    )
    
    return FileUploadInitResponse(
        upload_id=upload_id,
        chunk_size=chunk_size,
        total_chunks=upload_data.total_chunks
    )


@router.post("/upload/chunk")
async def upload_chunk(
    upload_id: str = Query(...),
    chunk_number: int = Query(..., ge=0),
    checksum: str = Query(...),
    filename: str = Query(...),
    total_chunks: int = Query(..., gt=0),
    chunk_file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file chunk"""
    # Read chunk data
    chunk_data = await chunk_file.read()
    
    try:
        upload_uuid = uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload ID")
    
    success = await FileService.upload_chunk(
        db=db,
        upload_id=upload_uuid,
        chunk_number=chunk_number,
        chunk_data=chunk_data,
        filename=filename,
        total_chunks=total_chunks,
        checksum=checksum
    )
    
    return {
        "success": success,
        "chunk_number": chunk_number,
        "message": f"Chunk {chunk_number + 1}/{total_chunks} uploaded successfully"
    }


@router.post("/upload/complete", response_model=FileResponse)
async def complete_upload(
    upload_data: FileUploadComplete,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete a chunked file upload"""
    # Get first chunk to get filename
    from app.models.sync import UploadChunk
    from sqlalchemy import select
    
    result = await db.execute(
        select(UploadChunk)
        .where(UploadChunk.upload_id == upload_data.upload_id)
        .limit(1)
    )
    chunk = result.scalar_one_or_none()
    
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    try:
        file_record = await FileService.complete_upload(
            db=db,
            upload_id=upload_data.upload_id,
            filename=chunk.filename,
            final_checksum=upload_data.final_checksum,
            user_id=current_user.id,
            mime_type=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return FileResponse(
        id=file_record.id,
        filename=file_record.filename,
        size=file_record.size,
        checksum=file_record.checksum,
        mime_type=file_record.mime_type,
        uploaded_by=file_record.uploaded_by,
        uploader_username=current_user.username,
        upload_date=file_record.upload_date,
        is_deleted=file_record.is_deleted,
        sync_status=file_record.sync_status.value
    )


@router.post("/upload/cancel")
async def cancel_upload(
    upload_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an ongoing upload"""
    try:
        upload_uuid = uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload ID")
    
    success = await FileService.cancel_upload(db=db, upload_id=upload_uuid)
    
    return {
        "success": success,
        "message": "Upload cancelled successfully"
    }


@router.get("", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    sort_by: str = Query("upload_date", regex="^(filename|size|upload_date)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = None,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List files with pagination and sorting"""
    files, total = await FileService.list_files(
        db=db,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search_query=search,
        include_deleted=include_deleted
    )
    
    # Convert to response format
    from sqlalchemy import select
    from app.models.user import User as UserModel
    
    items = []
    for file in files:
        # Get uploader username
        result = await db.execute(
            select(UserModel).where(UserModel.id == file.uploaded_by)
        )
        uploader = result.scalar_one_or_none()
        uploader_username = uploader.username if uploader else "Unknown"
        
        items.append(FileResponse(
            id=file.id,
            filename=file.filename,
            size=file.size,
            checksum=file.checksum,
            mime_type=file.mime_type,
            uploaded_by=file.uploaded_by,
            uploader_username=uploader_username,
            upload_date=file.upload_date,
            is_deleted=file.is_deleted,
            sync_status=file.sync_status.value
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return FileListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get file metadata"""
    file_record = await FileService.get_file(db=db, file_id=file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Get uploader username
    from sqlalchemy import select
    from app.models.user import User as UserModel
    
    result = await db.execute(
        select(UserModel).where(UserModel.id == file_record.uploaded_by)
    )
    uploader = result.scalar_one_or_none()
    uploader_username = uploader.username if uploader else "Unknown"
    
    return FileResponse(
        id=file_record.id,
        filename=file_record.filename,
        size=file_record.size,
        checksum=file_record.checksum,
        mime_type=file_record.mime_type,
        uploaded_by=file_record.uploaded_by,
        uploader_username=uploader_username,
        upload_date=file_record.upload_date,
        is_deleted=file_record.is_deleted,
        sync_status=file_record.sync_status.value
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Download a single file"""
    file_record = await FileService.get_file(db=db, file_id=file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(file_record.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=file_record.filepath,
        filename=file_record.filename,
        media_type=file_record.mime_type or "application/octet-stream"
    )


@router.post("/download/bulk")
async def bulk_download(
    download_request: BulkDownloadRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Download multiple files as a ZIP archive"""
    # Get all files
    files = []
    for file_id in download_request.file_ids:
        file_record = await FileService.get_file(db=db, file_id=file_id)
        if file_record and os.path.exists(file_record.filepath):
            files.append(file_record)
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No files found"
        )
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_record in files:
            zip_file.write(file_record.filepath, file_record.filename)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=files.zip"}
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a file"""
    try:
        file_record = await FileService.soft_delete_file(
            db=db,
            file_id=file_id,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {
        "success": True,
        "message": f"File '{file_record.filename}' deleted successfully"
    }


@router.post("/{file_id}/restore")
async def restore_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Restore a soft-deleted file"""
    try:
        file_record = await FileService.restore_file(db=db, file_id=file_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {
        "success": True,
        "message": f"File '{file_record.filename}' restored successfully"
    }


@router.put("/{file_id}/rename")
async def rename_file(
    file_id: uuid.UUID,
    rename_data: FileRenameRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Rename a file"""
    try:
        file_record = await FileService.rename_file(
            db=db,
            file_id=file_id,
            new_filename=rename_data.new_filename
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {
        "success": True,
        "message": f"File renamed to '{file_record.filename}' successfully"
    }


@router.get("/check-duplicate/{filename}")
async def check_duplicate(
    filename: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if a filename already exists"""
    existing_file = await FileService.check_duplicate(
        db=db,
        filename=filename,
        include_deleted=False
    )
    
    return {
        "exists": existing_file is not None,
        "file_id": str(existing_file.id) if existing_file else None
    }


@router.get("/deleted")
async def list_deleted_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List deleted files"""
    files, total = await FileService.list_files(
        db=db,
        page=page,
        page_size=page_size,
        include_deleted=True
    )
    
    # Filter only deleted files
    deleted_files = [f for f in files if f.is_deleted]
    
    # Convert to response format
    from sqlalchemy import select
    from app.models.user import User as UserModel
    
    items = []
    for file in deleted_files:
        result = await db.execute(
            select(UserModel).where(UserModel.id == file.uploaded_by)
        )
        uploader = result.scalar_one_or_none()
        uploader_username = uploader.username if uploader else "Unknown"
        
        items.append(FileResponse(
            id=file.id,
            filename=file.filename,
            size=file.size,
            checksum=file.checksum,
            mime_type=file.mime_type,
            uploaded_by=file.uploaded_by,
            uploader_username=uploader_username,
            upload_date=file.upload_date,
            is_deleted=file.is_deleted,
            sync_status=file.sync_status.value
        ))
    
    total_pages = (len(deleted_files) + page_size - 1) // page_size
    
    return FileListResponse(
        items=items,
        total=len(deleted_files),
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
