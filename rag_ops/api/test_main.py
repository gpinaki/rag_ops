# test_main.py

import pytest
from httpx import AsyncClient
from fastapi import status
from api.main import app

@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_list_files_empty():
    """Test listing files when no files are uploaded"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/files")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

@pytest.mark.asyncio
async def test_upload_file():
    """Test uploading a valid file"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        file_data = {"file": ("test_file.pdf", b"dummy content", "application/pdf")}
        response = await client.post("/upload", files=file_data)
    assert response.status_code == status.HTTP_201_CREATED
    uploaded_file = response.json()
    assert uploaded_file["filename"] == "test_file.pdf"
    assert uploaded_file["file_type"] == "pdf"

@pytest.mark.asyncio
async def test_get_file_by_id():
    """Test retrieving an uploaded file by ID"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First, upload a file
        file_data = {"file": ("test_file_2.pdf", b"dummy content", "application/pdf")}
        upload_response = await client.post("/upload", files=file_data)
        file_id = upload_response.json()["id"]

        # Retrieve the uploaded file
        response = await client.get(f"/files/{file_id}")
    assert response.status_code == status.HTTP_200_OK
    retrieved_file = response.json()
    assert retrieved_file["filename"] == "test_file_2.pdf"

@pytest.mark.asyncio
async def test_delete_file():
    """Test deleting an uploaded file"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First, upload a file
        file_data = {"file": ("test_file_3.pdf", b"dummy content", "application/pdf")}
        upload_response = await client.post("/upload", files=file_data)
        file_id = upload_response.json()["id"]

        # Delete the uploaded file
        response = await client.delete(f"/files/{file_id}")
    assert response.status_code == status.HTTP_200_OK
    delete_response = response.json()
    assert delete_response["message"] == f"File {file_id} deleted successfully"
