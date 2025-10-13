"""Tests for CandidateService"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Candidate, Education, WorkExperience, Skill, CandidateSkill
from models.candidate_schemas import ParsedResumeData, PersonalInfo, EducationData, WorkExperienceData, SkillData
from services.candidate_service import CandidateService


@pytest.fixture
async def db_session():
    """Create a test database session"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def sample_parsed_data():
    """Sample parsed resume data"""
    return ParsedResumeData(
        personal_info=PersonalInfo(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1-555-123-4567",
            linkedin_url="linkedin.com/in/johndoe",
            location="San Francisco, CA",
            confidence={"name": 0.98, "email": 1.0, "phone": 0.95}
        ),
        education=[
            EducationData(
                degree="Bachelor of Science",
                field="Computer Science",
                institution="Stanford University",
                location="Stanford, CA",
                start_date="2015-09",
                end_date="2019-06",
                gpa="3.8",
                confidence=0.92
            )
        ],
        experience=[
            WorkExperienceData(
                company="Google",
                title="Senior Software Engineer",
                location="Mountain View, CA",
                start_date="2021-03",
                end_date="Present",
                duration_months=42,
                description="Led development of...",
                achievements=["Improved system performance by 40%"],
                confidence=0.95
            )
        ],
        skills=[
            SkillData(name="Python", category="technical", proficiency="expert", confidence=0.98),
            SkillData(name="Java", category="technical", proficiency="expert", confidence=0.95)
        ],
        certifications=[],
        total_experience_months=60
    )


@pytest.mark.asyncio
async def test_create_candidate_from_parsed_data(db_session: AsyncSession, sample_parsed_data: ParsedResumeData):
    """Test creating a candidate from parsed data"""
    service = CandidateService(db_session)
    
    candidate_id = await service.create_candidate_from_parsed_data(
        parsed_data=sample_parsed_data,
        created_by="test-user-id"
    )
    
    assert candidate_id is not None
    
    # Verify candidate was created
    candidate = await service.get_candidate_by_id(candidate_id, include_relations=True)
    assert candidate is not None
    assert candidate["full_name"] == "John Doe"
    assert candidate["email"] == "john.doe@example.com"
    assert candidate["phone"] == "+1-555-123-4567"
    assert len(candidate["education"]) == 1
    assert len(candidate["experience"]) == 1
    assert len(candidate["skills"]) == 2


@pytest.mark.asyncio
async def test_get_candidate_by_id(db_session: AsyncSession, sample_parsed_data: ParsedResumeData):
    """Test retrieving a candidate by ID"""
    service = CandidateService(db_session)
    
    # Create candidate
    candidate_id = await service.create_candidate_from_parsed_data(
        parsed_data=sample_parsed_data,
        created_by="test-user-id"
    )
    
    # Retrieve candidate
    candidate = await service.get_candidate_by_id(candidate_id, include_relations=True)
    
    assert candidate is not None
    assert candidate["id"] == candidate_id
    assert candidate["full_name"] == "John Doe"
    assert "education" in candidate
    assert "experience" in candidate
    assert "skills" in candidate


@pytest.mark.asyncio
async def test_search_candidates(db_session: AsyncSession, sample_parsed_data: ParsedResumeData):
    """Test searching candidates"""
    service = CandidateService(db_session)
    
    # Create multiple candidates
    await service.create_candidate_from_parsed_data(
        parsed_data=sample_parsed_data,
        created_by="test-user-id"
    )
    
    # Search by name
    results = await service.search_candidates(search="John", page=1, limit=20)
    
    assert results is not None
    assert "candidates" in results
    assert "pagination" in results
    assert len(results["candidates"]) > 0
    assert results["candidates"][0]["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_update_candidate(db_session: AsyncSession, sample_parsed_data: ParsedResumeData):
    """Test updating a candidate"""
    from models.candidate_schemas import CandidateUpdate
    
    service = CandidateService(db_session)
    
    # Create candidate
    candidate_id = await service.create_candidate_from_parsed_data(
        parsed_data=sample_parsed_data,
        created_by="test-user-id"
    )
    
    # Update candidate
    update_data = CandidateUpdate(
        full_name="John Smith",
        location="New York, NY"
    )
    
    updated = await service.update_candidate(candidate_id, update_data)
    
    assert updated is not None
    assert updated["full_name"] == "John Smith"
    assert updated["location"] == "New York, NY"


@pytest.mark.asyncio
async def test_delete_candidate(db_session: AsyncSession, sample_parsed_data: ParsedResumeData):
    """Test deleting (archiving) a candidate"""
    service = CandidateService(db_session)
    
    # Create candidate
    candidate_id = await service.create_candidate_from_parsed_data(
        parsed_data=sample_parsed_data,
        created_by="test-user-id"
    )
    
    # Delete candidate
    success = await service.delete_candidate(candidate_id, deleted_by="test-user-id")
    
    assert success is True
    
    # Verify candidate is archived
    candidate = await service.get_candidate_by_id(candidate_id, include_relations=False)
    assert candidate["status"] == "archived"


@pytest.mark.asyncio
async def test_search_with_filters(db_session: AsyncSession, sample_parsed_data: ParsedResumeData):
    """Test searching candidates with filters"""
    service = CandidateService(db_session)
    
    # Create candidate
    await service.create_candidate_from_parsed_data(
        parsed_data=sample_parsed_data,
        created_by="test-user-id"
    )
    
    # Search with status filter
    results = await service.search_candidates(status="new", page=1, limit=20)
    
    assert results is not None
    assert len(results["candidates"]) > 0
    assert results["candidates"][0]["status"] == "new"


@pytest.mark.asyncio
async def test_create_candidate_with_minimal_data(db_session: AsyncSession):
    """Test creating a candidate with minimal data"""
    service = CandidateService(db_session)
    
    minimal_data = ParsedResumeData(
        personal_info=PersonalInfo(
            name="Jane Doe",
            email=None,
            phone=None,
            linkedin_url=None,
            location=None,
            confidence={}
        ),
        education=[],
        experience=[],
        skills=[],
        certifications=[],
        total_experience_months=None
    )
    
    candidate_id = await service.create_candidate_from_parsed_data(
        parsed_data=minimal_data,
        created_by="test-user-id"
    )
    
    assert candidate_id is not None
    
    candidate = await service.get_candidate_by_id(candidate_id, include_relations=True)
    assert candidate["full_name"] == "Jane Doe"
    assert candidate["email"] is None
