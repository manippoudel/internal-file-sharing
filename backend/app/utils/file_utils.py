"""File utilities for checksums and file operations"""
import hashlib
import os
import aiofiles
from typing import BinaryIO


async def calculate_checksum(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal checksum string
    """
    sha256 = hashlib.sha256()
    
    async with aiofiles.open(file_path, 'rb') as f:
        while True:
            chunk = await f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    
    return sha256.hexdigest()


async def calculate_checksum_from_stream(stream: BinaryIO, chunk_size: int = 8192) -> str:
    """
    Calculate SHA-256 checksum from a stream
    
    Args:
        stream: File stream
        chunk_size: Size of chunks to read
        
    Returns:
        Hexadecimal checksum string
    """
    sha256 = hashlib.sha256()
    
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        sha256.update(chunk)
    
    return sha256.hexdigest()


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()


def is_safe_path(base_path: str, path: str) -> bool:
    """
    Check if a path is safe (no directory traversal)
    
    Args:
        base_path: Base directory path
        path: Path to check
        
    Returns:
        True if path is safe, False otherwise
    """
    # Resolve both paths to absolute paths
    abs_base = os.path.abspath(base_path)
    abs_path = os.path.abspath(os.path.join(base_path, path))
    
    # Check if the resolved path starts with the base path
    return abs_path.startswith(abs_base)


async def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        directory: Directory path
    """
    os.makedirs(directory, exist_ok=True)
