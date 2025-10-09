"""Integration tests for job API endpoints"""
import pytest
from httpx import AsyncClient
from datetime import date

from main import app
from models.database import Base, User
from core.database import engine
from services.token_service import TokenService


@pytest.fixture
async def test_client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def setup_database():
    """Setup test database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def auth_headers():
    """Create authentication headers"""
    token_service = TokenService()
    
    # Create test user token
    access_token = token_service.create_access_token(
        user_id="test-user-1",
        email="manager@test.com",
        role="manager"
    )
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_job_payload():
    """Sample job creation payload"""
    return {
        "title": "Senior Software Engineer",
        "department": "Engineering",
        "location": {
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "is_remote": False
        },
        "work_type": "hybrid",
        "employment_type": "full_time",
        "num_openings": 2,
        "salary_range": {
            "min": 150000,
            "max": 200000,
            "currency": "USD",
            "period": "annual"
        },
        "description": "We are seeking a talented Senior Software Engineer to join our team.",
        "responsibilities": [
            "Design and develop scalable systems",
            "Lead technical architecture decisions"
        ],
        "requirements": {
            "mandatory": ["5+ years software development"],
            "preferred": ["Cloud platforms"]
        },
        "skills": [
            {
                "name": "Python",
                "is_mandatory": True,
                "proficiency_level": "expert"
            }
        ],
        "closing_date": "2025-12-31",
        "status": "draft"
    }


# ============================================================================
# CREATE JOB TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_job_success(test_client, auth_headers, sample_job_payload, setup_database):
    """Test successful job creation"""
    response = await test_client.post(
        "/api/jobs",
        json=sample_job_payload,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Job created successfully"
    assert data["data"]["title"] == "Senior Software Engineer"


@pytest.mark.asyncio
async def test_create_job_unauthorized(test_client, sample_job_payload):
    """Test creating job without authentication fails"""
    response = await test_client.post(
        "/api/jobs",
        json=sample_job_payload
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_job_validation_error(test_client, auth_headers, setup_database):
    """Test creating job with invalid data"""
    invalid_payload = {
        "title": "AB",  # Too short
        "description": "Short"  # Too short
    }
    
    response = await test_client.post(
        "/api/jobs",
        json=invalid_payload,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


# ============================================================================
# LIST JOBS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_jobs(test_client, auth_headers, setup_database):
    """Test listing jobs"""
    response = await test_client.get(
        "/api/jobs",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "jobs" in data["data"]
    assert "total" in data["data"]


@pytest.mark.asyncio
async def test_list_jobs_with_filters(test_client, auth_headers, setup_database):
    """Test listing jobs with filters"""
    response = await test_client.get(
        "/api/jobs?status=open&department=Engineering",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_list_jobs_pagination(test_client, auth_headers, setup_database):
    """Test job list pagination"""
    response = await test_client.get(
        "/api/jobs?page=1&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["page"] == 1
    assert data["data"]["limit"] == 10


# ============================================================================
# GET JOB TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_job_not_found(test_client, auth_headers, setup_database):
    """Test getting non-existent job"""
    response = await test_client.get(
        "/api/jobs/nonexistent-id",
        headers=auth_headers
    )
    
    assert response.status_code == 404


# ============================================================================
# UPDATE JOB TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_job_not_found(test_client, auth_headers, setup_database):
    """Test updating non-existent job"""
    update_payload = {"title": "New Title"}
    
    response = await test_client.patch(
        "/api/jobs/nonexistent-id",
        json=update_payload,
        headers=auth_headers
    )
    
    assert response.status_code == 404


# ============================================================================
# DELETE JOB TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_job_not_found(test_client, auth_headers, setup_database):
    """Test deleting non-existent job"""
    response = await test_client.delete(
        "/api/jobs/nonexistent-id",
        headers=auth_headers
    )
    
    assert response.status_code == 404


# ============================================================================
# WORKFLOW TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_publish_job_not_found(test_client, auth_headers, setup_database):
    """Test publishing non-existent job"""
    response = await test_client.post(
        "/api/jobs/nonexistent-id/publish",
        json={"send_notifications": False},
        headers=auth_headers
    )
    
    assert response.status_code in [400, 404, 500]


@pytest.mark.asyncio
async def test_close_job_not_found(test_client, auth_headers, setup_database):
    """Test closing non-existent job"""
    response = await test_client.post(
        "/api/jobs/nonexistent-id/close",
        json={"close_reason": "filled", "notes": "Position filled"},
        headers=auth_headers
    )
    
    assert response.status_code in [400, 404, 500]


# ============================================================================
# STATISTICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_job_statistics(test_client, auth_headers, setup_database):
    """Test getting job statistics"""
    response = await test_client.get(
        "/api/jobs/stats/overview",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "total_jobs" in data["data"]
    assert "by_status" in data["data"]
