"""File schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import uuid


class FileUploadInit(BaseModel):
    """Initialize chunked file upload"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    total_chunks: int = Field(..., gt=0)
    mime_type: Optional[str] = None
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        """Validate filename security"""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Filename cannot contain path separators")
        if "\x00" in v:
            raise ValueError("Filename cannot contain null bytes")
        return v


class FileUploadInitResponse(BaseModel):
    """Response for upload initialization"""
    upload_id: uuid.UUID
    chunk_size: int
    total_chunks: int


class FileUploadChunk(BaseModel):
    """Upload file chunk"""
    upload_id: uuid.UUID
    chunk_number: int = Field(..., ge=0)
    checksum: str = Field(..., min_length=64, max_length=64)


class FileUploadComplete(BaseModel):
    """Complete file upload"""
    upload_id: uuid.UUID
    final_checksum: str = Field(..., min_length=64, max_length=64)


class FileResponse(BaseModel):
    """File metadata response"""
    id: uuid.UUID
    filename: str
    size: int
    checksum: str
    mime_type: Optional[str]
    uploaded_by: uuid.UUID
    uploader_username: str
    upload_date: datetime
    is_deleted: bool
    sync_status: str
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """File list response with pagination"""
    items: List[FileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FileSearchRequest(BaseModel):
    """File search and filter request"""
    query: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None
    uploader_id: Optional[uuid.UUID] = None
    mime_type: Optional[str] = None
    include_deleted: bool = False


class FileRenameRequest(BaseModel):
    """File rename request"""
    new_filename: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('new_filename')
    @classmethod
    def validate_filename(cls, v):
        """Validate filename security"""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Filename cannot contain path separators")
        if "\x00" in v:
            raise ValueError("Filename cannot contain null bytes")
        return v


class BulkDownloadRequest(BaseModel):
    """Bulk download request"""
    file_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100)
