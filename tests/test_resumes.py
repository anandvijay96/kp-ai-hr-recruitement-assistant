from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

def test_upload_single_resume_success():
    """Test successful single resume upload."""
    file_content = b"dummy pdf content"
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["file_name"] == "test.pdf"
    assert data["status"] == "processing"

def test_upload_single_resume_invalid_type():
    """Test single resume upload with an invalid file type."""
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("test.txt", io.BytesIO(b"some text"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_upload_batch_resume_success():
    """Test successful batch resume upload."""
    files = [
        ("files", ("test1.pdf", io.BytesIO(b"pdf1"), "application/pdf")),
        ("files", ("test2.docx", io.BytesIO(b"docx2"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    ]
    response = client.post("/api/v1/resumes/upload-batch", files=files)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["file_name"] == "test1.pdf"
    assert data[1]["file_name"] == "test2.docx"

def test_get_job_status_not_found():
    """Test getting status for a non-existent job."""
    response = client.get("/api/v1/resumes/jobs/non-existent-job")
    assert response.status_code == 404
