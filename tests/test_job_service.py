"""Unit tests for job service"""
import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Job, User, Skill
from services.job_service import JobService
from models.job_schemas import (
    JobCreateRequest, JobUpdateRequest, LocationModel, SalaryRangeModel,
    RequirementsModel, JobSkillModel, RecruiterAssignmentModel,
    WorkType, EmploymentType, JobStatus, ProficiencyLevel
)


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Create a test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create test user
        user = User(
            id="test-user-1",
            full_name="Test Manager",
            email="manager@test.com",
            mobile="1234567890",
            password_hash="hashed",
            role="manager",
            is_active=True,
            email_verified=True
        )
        session.add(user)
        
        # Create test skill
        skill = Skill(
            id="skill-1",
            name="Python",
            category="technical"
        )
        session.add(skill)
        
        await session.commit()
        
        yield session
    
    await engine.dispose()


@pytest.fixture
def job_service(db_session):
    """Create job service instance"""
    return JobService(db_session=db_session)


@pytest.fixture
def sample_job_data():
    """Sample job creation data"""
    return JobCreateRequest(
        title="Senior Software Engineer",
        department="Engineering",
        location=LocationModel(
            city="San Francisco",
            state="CA",
            country="USA",
            is_remote=False
        ),
        work_type=WorkType.HYBRID,
        employment_type=EmploymentType.FULL_TIME,
        num_openings=2,
        salary_range=SalaryRangeModel(
            min=150000,
            max=200000,
            currency="USD",
            period="annual"
        ),
        description="We are seeking a talented Senior Software Engineer to join our team.",
        responsibilities=[
            "Design and develop scalable systems",
            "Lead technical architecture decisions"
        ],
        requirements=RequirementsModel(
            mandatory=["5+ years software development", "Expert in Python/Java"],
            preferred=["Cloud platforms (AWS/Azure)"]
        ),
        skills=[
            JobSkillModel(
                name="Python",
                is_mandatory=True,
                proficiency_level=ProficiencyLevel.EXPERT
            )
        ],
        closing_date=date(2025, 12, 31),
        status=JobStatus.DRAFT
    )


# ============================================================================
# CREATE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_job_success(job_service, sample_job_data):
    """Test successful job creation"""
    job = await job_service.create_job(
        job_data=sample_job_data,
        created_by="test-user-1"
    )
    
    assert job is not None
    assert job["title"] == "Senior Software Engineer"
    assert job["department"] == "Engineering"
    assert job["status"] == "draft"
    assert job["num_openings"] == 2
    assert len(job["skills"]) == 1
    assert job["skills"][0]["name"] == "Python"


@pytest.mark.asyncio
async def test_create_job_with_published_status(job_service, sample_job_data):
    """Test creating job with published status sets published_at"""
    sample_job_data.status = JobStatus.OPEN
    
    job = await job_service.create_job(
        job_data=sample_job_data,
        created_by="test-user-1"
    )
    
    assert job["status"] == "open"
    assert job["published_at"] is not None


# ============================================================================
# READ TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_job_by_id(job_service, sample_job_data):
    """Test getting job by ID"""
    created_job = await job_service.create_job(
        job_data=sample_job_data,
        created_by="test-user-1"
    )
    
    job = await job_service.get_job_by_id(
        job_id=created_job["id"],
        include_relations=True
    )
    
    assert job is not None
    assert job["id"] == created_job["id"]
    assert job["title"] == "Senior Software Engineer"
    assert "skills" in job
    assert "assigned_recruiters" in job


@pytest.mark.asyncio
async def test_get_nonexistent_job(job_service):
    """Test getting non-existent job returns None"""
    job = await job_service.get_job_by_id(
        job_id="nonexistent-id",
        include_relations=False
    )
    
    assert job is None


@pytest.mark.asyncio
async def test_search_jobs(job_service, sample_job_data):
    """Test searching jobs"""
    # Create multiple jobs
    await job_service.create_job(sample_job_data, "test-user-1")
    
    sample_job_data.title = "Junior Developer"
    sample_job_data.department = "Engineering"
    await job_service.create_job(sample_job_data, "test-user-1")
    
    # Search all jobs
    result = await job_service.search_jobs(
        page=1,
        limit=10,
        user_id="test-user-1",
        user_role="manager"
    )
    
    assert result["total"] == 2
    assert len(result["jobs"]) == 2
    assert result["total_pages"] == 1


@pytest.mark.asyncio
async def test_search_jobs_with_filters(job_service, sample_job_data):
    """Test searching jobs with filters"""
    await job_service.create_job(sample_job_data, "test-user-1")
    
    sample_job_data.title = "Marketing Manager"
    sample_job_data.department = "Marketing"
    await job_service.create_job(sample_job_data, "test-user-1")
    
    # Search by department
    result = await job_service.search_jobs(
        department="Engineering",
        page=1,
        limit=10,
        user_id="test-user-1",
        user_role="manager"
    )
    
    assert result["total"] == 1
    assert result["jobs"][0]["department"] == "Engineering"


# ============================================================================
# UPDATE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_job(job_service, sample_job_data):
    """Test updating job"""
    job = await job_service.create_job(sample_job_data, "test-user-1")
    
    update_data = JobUpdateRequest(
        title="Staff Software Engineer",
        num_openings=3
    )
    
    updated_job = await job_service.update_job(
        job_id=job["id"],
        update_data=update_data
    )
    
    assert updated_job["title"] == "Staff Software Engineer"
    assert updated_job["num_openings"] == 3
    assert updated_job["department"] == "Engineering"  # Unchanged


@pytest.mark.asyncio
async def test_update_nonexistent_job(job_service):
    """Test updating non-existent job raises error"""
    update_data = JobUpdateRequest(title="New Title")
    
    with pytest.raises(ValueError, match="Job not found"):
        await job_service.update_job(
            job_id="nonexistent-id",
            update_data=update_data
        )


# ============================================================================
# DELETE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_draft_job(job_service, sample_job_data):
    """Test deleting draft job"""
    job = await job_service.create_job(sample_job_data, "test-user-1")
    
    success = await job_service.delete_job(job["id"])
    
    assert success is True
    
    # Verify job is deleted
    deleted_job = await job_service.get_job_by_id(job["id"])
    assert deleted_job is None


@pytest.mark.asyncio
async def test_delete_published_job_fails(job_service, sample_job_data):
    """Test deleting published job fails"""
    sample_job_data.status = JobStatus.OPEN
    job = await job_service.create_job(sample_job_data, "test-user-1")
    
    with pytest.raises(ValueError, match="Only draft jobs can be deleted"):
        await job_service.delete_job(job["id"])


# ============================================================================
# WORKFLOW TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_publish_job(job_service, sample_job_data):
    """Test publishing draft job"""
    job = await job_service.create_job(sample_job_data, "test-user-1")
    
    published_job = await job_service.publish_job(
        job_id=job["id"],
        published_by="test-user-1",
        send_notifications=False
    )
    
    assert published_job["status"] == "open"
    assert published_job["published_at"] is not None


@pytest.mark.asyncio
async def test_publish_already_published_job_fails(job_service, sample_job_data):
    """Test publishing already published job fails"""
    sample_job_data.status = JobStatus.OPEN
    job = await job_service.create_job(sample_job_data, "test-user-1")
    
    with pytest.raises(ValueError, match="Only draft jobs can be published"):
        await job_service.publish_job(
            job_id=job["id"],
            published_by="test-user-1"
        )


@pytest.mark.asyncio
async def test_close_job(job_service, sample_job_data):
    """Test closing job"""
    sample_job_data.status = JobStatus.OPEN
    job = await job_service.create_job(sample_job_data, "test-user-1")
    
    closed_job = await job_service.close_job(
        job_id=job["id"],
        close_reason="filled",
        notes="Position filled",
        closed_by="test-user-1"
    )
    
    assert closed_job["status"] == "closed"
    assert closed_job["close_reason"] == "filled"
    assert closed_job["closed_at"] is not None


@pytest.mark.asyncio
async def test_reopen_job(job_service, sample_job_data):
    """Test reopening closed job"""
    sample_job_data.status = JobStatus.OPEN
    job = await job_service.create_job(sample_job_data, "test-user-1")
    
    # Close job
    await job_service.close_job(
        job_id=job["id"],
        close_reason="filled",
        notes=None,
        closed_by="test-user-1"
    )
    
    # Reopen job
    reopened_job = await job_service.reopen_job(
        job_id=job["id"],
        reopened_by="test-user-1"
    )
    
    assert reopened_job["status"] == "open"
    assert reopened_job["closed_at"] is None
    assert reopened_job["close_reason"] is None


# ============================================================================
# CLONE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_clone_job(job_service, sample_job_data):
    """Test cloning job"""
    original_job = await job_service.create_job(sample_job_data, "test-user-1")
    
    cloned_job = await job_service.clone_job(
        job_id=original_job["id"],
        new_title="Senior Software Engineer (Copy)",
        modify_fields=None,
        created_by="test-user-1"
    )
    
    assert cloned_job["id"] != original_job["id"]
    assert cloned_job["title"] == "Senior Software Engineer (Copy)"
    assert cloned_job["status"] == "draft"
    assert cloned_job["department"] == original_job["department"]
    assert len(cloned_job["skills"]) == len(original_job["skills"])


# ============================================================================
# STATISTICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_statistics(job_service, sample_job_data):
    """Test getting job statistics"""
    # Create jobs with different statuses
    await job_service.create_job(sample_job_data, "test-user-1")
    
    sample_job_data.status = JobStatus.OPEN
    await job_service.create_job(sample_job_data, "test-user-1")
    
    stats = await job_service.get_statistics(
        user_id="test-user-1",
        user_role="manager"
    )
    
    assert stats["total_jobs"] == 2
    assert "by_status" in stats
    assert "by_department" in stats
    assert stats["by_status"]["draft"] == 1
    assert stats["by_status"]["open"] == 1
