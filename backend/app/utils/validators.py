"""Validation utilities"""
import re
from typing import Optional


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format
    
    Args:
        username: Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be at most 50 characters long"
    
    # Only allow alphanumeric characters, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format
    
    Args:
        email: Email to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def validate_filename(filename: str) -> tuple[bool, str]:
    """
    Validate filename for security
    
    Args:
        filename: Filename to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"
    
    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False, "Filename cannot contain path separators"
    
    # Check for null bytes
    if "\x00" in filename:
        return False, "Filename cannot contain null bytes"
    
    # Check length
    if len(filename) > 255:
        return False, "Filename is too long (max 255 characters)"
    
    return True, ""
