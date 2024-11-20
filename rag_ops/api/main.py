# api/main.py

from fastapi import FastAPI, HTTPException, status, UploadFile, File
from typing import List, Dict, Any
from datetime import datetime
import os
import logging
import aiofiles
from .models import FileCreate, FileResponse, ErrorResponse
from .utils import (
    format_file_size,
    validate_file_type,
    validate_file_size,
    ALLOWED_FILE_TYPES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Document Management API",
    description="API for managing file uploads and processing",
    version="1.0.0"
)

# In-memory storage
files_db: Dict[int, Dict[str, Any]] = {}

@app.get(
    "/health",
    summary="Health Check",
    description="Check if the API is running",
    response_model=Dict[str, str]
)
def health_check() -> Dict[str, str]:
    """Basic health check endpoint"""
    return {"status": "healthy"}

@app.get(
    "/files",
    response_model=List[FileResponse],
    summary="List Files",
    description="Get a list of all files in the system",
    responses={
        200: {"description": "List of files retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def list_files() -> List[Dict[str, Any]]:
    """Get list of all files"""
    try:
        return list(files_db.values())
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get(
    "/files/{file_id}",
    response_model=FileResponse,
    summary="Get File",
    description="Get details of a specific file by ID",
    responses={
        200: {"description": "File details retrieved successfully"},
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def get_file(file_id: int) -> Dict[str, Any]:
    """Get a specific file by ID"""
    try:
        if file_id not in files_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found"
            )
        return files_db[file_id]
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload File",
    description=f"Upload a new file. Allowed types: {list(ALLOWED_FILE_TYPES.keys())}",
)
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a new file with content type validation"""
    try:
        # Validate file type and content type
        file_type = validate_file_type(file.filename, file.content_type)
        
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            file_size = len(content)
            
            # Validate file size
            validate_file_size(file_size, file_type)
            
            # Write file
            await f.write(content)
        
        # Create file entry
        file_id = len(files_db) + 1
        new_file = {
            "id": file_id,
            "filename": file.filename,
            "file_type": file_type,
            "content_type": file.content_type,
            "size": file_size,
            "size_formatted": format_file_size(file_size),
            "upload_time": datetime.now(),
            "status": "uploaded",
            "file_path": file_path,
            "error_message": None
        }
        
        files_db[file_id] = new_file
        logger.info(f"File uploaded successfully: {file_path}")
        return new_file
        
    except HTTPException as e:
        logger.error(f"Upload failed: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        await file.seek(0)  # Reset file pointer

@app.delete(
    "/files/{file_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete File",
    description="Delete a file by ID and remove it from storage",
    responses={
        200: {
            "description": "File deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "File deleted successfully",
                        "details": {
                            "filename": "example.pdf",
                            "size_freed": "1.5 MB"
                        }
                    }
                }
            }
        },
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_file(file_id: int) -> Dict[str, Any]:
    """Delete a file and remove it from storage"""
    try:
        if file_id not in files_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found"
            )

        file_info = files_db[file_id]
        file_path = file_info.get("file_path")
        
        if file_path and os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                logger.info(f"Physical file deleted: {file_path}")
                
                del files_db[file_id]
                
                return {
                    "message": f"File {file_id} deleted successfully",
                    "details": {
                        "filename": file_info["filename"],
                        "size_freed": format_file_size(file_size)
                    }
                }
            except OSError as e:
                logger.error(f"Error deleting file {file_path}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error deleting physical file: {str(e)}"
                )
        else:
            del files_db[file_id]
            logger.warning(f"No physical file found for ID {file_id}, removed from database only")
            
            return {
                "message": f"File {file_id} record deleted successfully",
                "details": {
                    "filename": file_info["filename"],
                    "note": "No physical file was found"
                }
            }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error deleting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file deletion: {str(e)}"
        )