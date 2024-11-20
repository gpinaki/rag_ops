# api/models.py

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from .utils import ALLOWED_FILE_TYPES

class FileCreate(BaseModel):
    """Request model for file creation"""
    filename: str = Field(..., description="Name of the file", min_length=1)
    file_type: str = Field(..., description="Type of file (pdf, csv, etc)")
    content_type: str = Field(..., description="MIME type of the file")
    size: Optional[int] = Field(None, description="Size of file in bytes")

    @validator('file_type')
    def validate_file_type(cls, v):
        if v not in ALLOWED_FILE_TYPES:
            raise ValueError(f"File type not allowed. Allowed types: {list(ALLOWED_FILE_TYPES.keys())}")
        return v

    @validator('content_type')
    def validate_content_type(cls, v, values):
        if 'file_type' in values:
            if v not in ALLOWED_FILE_TYPES[values['file_type']]:
                raise ValueError(f"Invalid content type for file type {values['file_type']}")
        return v

class FileResponse(BaseModel):
    """Response model for file operations"""
    id: int = Field(..., description="Unique identifier for the file")
    filename: str = Field(..., description="Name of the file")
    file_type: str = Field(..., description="Type of file")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="Size of file in bytes")
    size_formatted: str = Field(..., description="Formatted file size (KB/MB/GB)")
    upload_time: datetime = Field(..., description="Time of upload")
    status: str = Field(..., description="Current status of the file")
    error_message: Optional[str] = Field(None, description="Error message if any")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")