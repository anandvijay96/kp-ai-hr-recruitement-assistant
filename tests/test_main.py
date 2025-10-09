import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_home_page():
    """Test home page loads"""
    response = client.get("/")
    assert response.status_code == 200

def test_upload_page():
    """Test upload page loads"""
    response = client.get("/upload")
    assert response.status_code == 200

def test_scan_resume_without_file():
    """Test scan resume endpoint without file"""
    response = client.post("/api/scan-resume")
    assert response.status_code == 422  # Validation error

def test_batch_scan_without_files():
    """Test batch scan endpoint without files"""
    response = client.post("/api/batch-scan")
    assert response.status_code == 422  # Validation error
