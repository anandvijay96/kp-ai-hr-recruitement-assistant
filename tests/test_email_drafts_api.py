from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_email_drafts_db_endpoint_requires_auth():
    """POST /api/v1/email-drafts should reject unauthenticated access with 401."""

    response = client.post("/api/v1/email-drafts")
    # Endpoint is protected by get_current_user_or_redirect, so unauthenticated
    # requests should fail with 401 before body validation occurs.
    assert response.status_code == 401


def test_email_drafts_from_uploads_requires_auth(tmp_path):
    """Upload-based endpoint should reject unauthenticated access with 401."""

    data = {
        "client_name": "Test Client",
        "job_description_text": "Sample JD for testing",
    }

    files = {
        "files": ("resume.pdf", b"dummy content", "application/pdf"),
    }

    response = client.post(
        "/api/v1/email-drafts/from-uploads",
        data=data,
        files=files,
    )

    # get_current_user_or_redirect should reject when no session user is present
    assert response.status_code == 401
