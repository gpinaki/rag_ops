# api/utils.py

# api/utils.py

from typing import Dict, Set
from fastapi import HTTPException, status

# Define allowed file types and their corresponding MIME types
ALLOWED_FILE_TYPES: Dict[str, Set[str]] = {
    "pdf": {"application/pdf"},
    "csv": {"text/csv", "application/csv"},
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel"
    }
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES: Dict[str, int] = {
    "pdf": 20 * 1024 * 1024,  # 20MB
    "csv": 10 * 1024 * 1024,  # 10MB
    "xlsx": 15 * 1024 * 1024  # 15MB
}

def format_file_size(size_in_bytes: int) -> str:
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            if unit == 'B':
                return f"{size_in_bytes} {unit}"
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"

def validate_file_type(filename: str, content_type: str) -> str:
    """
    Validate file type based on extension and MIME type
    
    Args:
        filename (str): Name of the file
        content_type (str): MIME type of the file
        
    Returns:
        str: Validated file type
        
    Raises:
        HTTPException: If file type is not valid
    """
    # Get file extension
    try:
        file_ext = filename.rsplit(".", 1)[1].lower()
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension"
        )

    # Check if extension is allowed
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{file_ext}' not allowed. Allowed types: {list(ALLOWED_FILE_TYPES.keys())}"
        )

    # Validate MIME type
    if content_type not in ALLOWED_FILE_TYPES[file_ext]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type '{content_type}' for file type '{file_ext}'"
        )

    return file_ext

def validate_file_size(file_size: int, file_type: str) -> None:
    """
    Validate file size against maximum allowed size
    
    Args:
        file_size (int): Size of the file in bytes
        file_type (str): Type of the file
        
    Raises:
        HTTPException: If file size exceeds maximum allowed size
    """
    max_size = MAX_FILE_SIZES.get(file_type)
    if max_size and file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({format_file_size(file_size)}) exceeds maximum allowed size ({format_file_size(max_size)}) for {file_type} files"
        )
        