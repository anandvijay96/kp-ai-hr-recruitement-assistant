"""Tests for DuplicateDetectionService"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Candidate
from models.candidate_schemas import ParsedResumeData, PersonalInfo
from services.duplicate_detection_service import DuplicateDetectionService
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


@pytest.mark.asyncio
async def test_check_email_match(db_session: AsyncSession):
    """Test exact email match detection"""
    # Create existing candidate
    candidate_service = CandidateService(db_session)
    existing_data = ParsedResumeData(
        personal_info=PersonalInfo(
            name="John Doe",
            email="john.doe@example.com",
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
    
    await candidate_service.create_candidate_from_parsed_data(
        parsed_data=existing_data,
        created_by="test-user-id"
    )
    
    # Check for duplicate
    duplicate_service = DuplicateDetectionService(db_session)
    match = await duplicate_service.check_email_match("john.doe@example.com")
    
    assert match is not None
    assert match["email"] == "john.doe@example.com"
    assert match["match_type"] == "email"
    assert match["match_score"] == 1.0


@pytest.mark.asyncio
async def test_check_email_no_match(db_session: AsyncSession):
    """Test email match when no duplicate exists"""
    duplicate_service = DuplicateDetectionService(db_session)
    match = await duplicate_service.check_email_match("nonexistent@example.com")
    
    assert match is None


@pytest.mark.asyncio
async def test_check_phone_match(db_session: AsyncSession):
    """Test phone number match detection"""
    # Create existing candidate
    candidate_service = CandidateService(db_session)
    existing_data = ParsedResumeData(
        personal_info=PersonalInfo(
            name="Jane Smith",
            email=None,
            phone="+1-555-123-4567",
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
    
    await candidate_service.create_candidate_from_parsed_data(
        parsed_data=existing_data,
        created_by="test-user-id"
    )
    
    # Check for duplicate with different phone format
    duplicate_service = DuplicateDetectionService(db_session)
    match = await duplicate_service.check_phone_match("(555) 123-4567")
    
    assert match is not None
    assert match["match_type"] == "phone"
    assert match["match_score"] == 1.0


@pytest.mark.asyncio
async def test_normalize_phone(db_session: AsyncSession):
    """Test phone number normalization"""
    duplicate_service = DuplicateDetectionService(db_session)
    
    # Test various phone formats
    assert duplicate_service._normalize_phone("+1-555-123-4567") == "5551234567"
    assert duplicate_service._normalize_phone("(555) 123-4567") == "5551234567"
    assert duplicate_service._normalize_phone("555.123.4567") == "5551234567"
    assert duplicate_service._normalize_phone("5551234567") == "5551234567"


@pytest.mark.asyncio
async def test_normalize_email(db_session: AsyncSession):
    """Test email normalization"""
    duplicate_service = DuplicateDetectionService(db_session)
    
    assert duplicate_service._normalize_email("John.Doe@Example.COM") == "john.doe@example.com"
    assert duplicate_service._normalize_email("  test@test.com  ") == "test@test.com"
    assert duplicate_service._normalize_email(None) is None


@pytest.mark.asyncio
async def test_check_duplicates_comprehensive(db_session: AsyncSession):
    """Test comprehensive duplicate checking"""
    # Create existing candidate
    candidate_service = CandidateService(db_session)
    existing_data = ParsedResumeData(
        personal_info=PersonalInfo(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1-555-123-4567",
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
    
    await candidate_service.create_candidate_from_parsed_data(
        parsed_data=existing_data,
        created_by="test-user-id"
    )
    
    # Check for duplicate with same email
    duplicate_service = DuplicateDetectionService(db_session)
    new_data = ParsedResumeData(
        personal_info=PersonalInfo(
            name="John D.",
            email="john.doe@example.com",
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
    
    duplicates = await duplicate_service.check_duplicates(new_data)
    
    assert len(duplicates) > 0
    assert duplicates[0]["match_type"] == "email"
    assert duplicates[0]["match_score"] == 1.0


@pytest.mark.asyncio
async def test_log_duplicate_check(db_session: AsyncSession):
    """Test logging duplicate check"""
    from models.database import Resume
    import uuid
    
    # Create a resume record
    resume = Resume(
        id=str(uuid.uuid4()),
        file_name="test.pdf",
        original_file_name="test.pdf",
        file_path="/path/to/test.pdf",
        file_size=1024,
        file_type="pdf",
        file_hash="abc123",
        mime_type="application/pdf",
        uploaded_by="test-user-id"
    )
    db_session.add(resume)
    await db_session.commit()
    
    # Log duplicate check
    duplicate_service = DuplicateDetectionService(db_session)
    await duplicate_service.log_duplicate_check(
        resume_id=resume.id,
        match_type="email",
        match_score=1.0,
        matched_candidate_id="candidate-123"
    )
    
    # Verify log was created
    from sqlalchemy import select
    from models.database import DuplicateCheck
    
    result = await db_session.execute(
        select(DuplicateCheck).where(DuplicateCheck.resume_id == resume.id)
    )
    log = result.scalar_one_or_none()
    
    assert log is not None
    assert log.match_type == "email"
    assert log.match_score == "1.0"


@pytest.mark.asyncio
async def test_resolve_duplicate(db_session: AsyncSession):
    """Test resolving a duplicate"""
    from models.database import Resume, DuplicateCheck
    import uuid
    
    # Create resume and duplicate check
    resume = Resume(
        id=str(uuid.uuid4()),
        file_name="test.pdf",
        original_file_name="test.pdf",
        file_path="/path/to/test.pdf",
        file_size=1024,
        file_type="pdf",
        file_hash="abc123",
        mime_type="application/pdf",
        uploaded_by="test-user-id"
    )
    db_session.add(resume)
    await db_session.commit()
    
    duplicate_check = DuplicateCheck(
        id=str(uuid.uuid4()),
        resume_id=resume.id,
        match_type="email",
        match_score="1.0"
    )
    db_session.add(duplicate_check)
    await db_session.commit()
    
    # Resolve duplicate
    duplicate_service = DuplicateDetectionService(db_session)
    success = await duplicate_service.resolve_duplicate(
        resume_id=resume.id,
        resolution="skip",
        resolved_by="test-user-id"
    )
    
    assert success is True
    
    # Verify resolution
    await db_session.refresh(duplicate_check)
    assert duplicate_check.resolution == "skip"
    assert duplicate_check.resolved_by == "test-user-id"
    assert duplicate_check.resolved_at is not None
