"""Unit tests for Jobs Management Service"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Job, User, JobStatusHistory, generate_uuid
from services.jobs_management_service import JobsManagementService


# Test database setup
@pytest.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def test_user(db_session):
    """Create test user"""
    user = User(
        id=generate_uuid(),
        full_name="Test User",
        email="test@example.com",
        mobile="1234567890",
        password_hash="hashed_password",
        role="admin",
        is_active=True,
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_job(db_session, test_user):
    """Create test job"""
    job = Job(
        id=generate_uuid(),
        uuid=generate_uuid(),
        title="Software Engineer",
        department="Engineering",
        description="Test job description",
        status="open",
        work_type="remote",
        employment_type="full_time",
        created_by=test_user.id,
        view_count=0
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


class TestJobsManagementService:
    """Test cases for JobsManagementService"""
    
    @pytest.mark.asyncio
    async def test_get_dashboard(self, db_session, test_user, test_job):
        """Test dashboard retrieval"""
        service = JobsManagementService(db_session)
        
        result = await service.get_dashboard(
            user_id=test_user.id,
            user_role=test_user.role,
            page=1,
            limit=20
        )
        
        assert result["success"] is True
        assert len(result["jobs"]) == 1
        assert result["jobs"][0]["title"] == "Software Engineer"
        assert result["summary"]["total_jobs"] == 1
        assert result["summary"]["open"] == 1
    
    @pytest.mark.asyncio
    async def test_update_job_status_valid_transition(self, db_session, test_user, test_job):
        """Test valid status transition"""
        service = JobsManagementService(db_session)
        
        result = await service.update_job_status(
            job_id=test_job.id,
            new_status="on_hold",
            reason="Budget review",
            user_id=test_user.id,
            user_role=test_user.role
        )
        
        assert result["success"] is True
        assert result["status"] == "on_hold"
        assert result["old_status"] == "open"
    
    @pytest.mark.asyncio
    async def test_update_job_status_invalid_transition(self, db_session, test_user, test_job):
        """Test invalid status transition"""
        service = JobsManagementService(db_session)
        
        # Try to transition from open to archived (invalid)
        with pytest.raises(ValueError, match="Invalid status transition"):
            await service.update_job_status(
                job_id=test_job.id,
                new_status="archived",
                reason="Test",
                user_id=test_user.id,
                user_role=test_user.role
            )
    
    @pytest.mark.asyncio
    async def test_update_job_status_requires_reason_for_close(self, db_session, test_user, test_job):
        """Test that closing requires a reason"""
        service = JobsManagementService(db_session)
        
        with pytest.raises(ValueError, match="Reason is required"):
            await service.update_job_status(
                job_id=test_job.id,
                new_status="closed",
                reason=None,
                user_id=test_user.id,
                user_role=test_user.role
            )
    
    @pytest.mark.asyncio
    async def test_delete_job_soft_delete(self, db_session, test_user, test_job):
        """Test soft delete (archive)"""
        service = JobsManagementService(db_session)
        
        result = await service.delete_job(
            job_id=test_job.id,
            permanent=False,
            user_id=test_user.id
        )
        
        assert result["success"] is True
        assert result["deleted"] is False
        assert result["archived_at"] is not None
    
    @pytest.mark.asyncio
    async def test_increment_view_count(self, db_session, test_job):
        """Test view count increment"""
        service = JobsManagementService(db_session)
        
        initial_count = test_job.view_count
        await service.increment_view_count(test_job.id)
        
        await db_session.refresh(test_job)
        assert test_job.view_count == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_get_job_status_history(self, db_session, test_user, test_job):
        """Test status history retrieval"""
        # Create status change
        service = JobsManagementService(db_session)
        await service.update_job_status(
            job_id=test_job.id,
            new_status="on_hold",
            reason="Test reason",
            user_id=test_user.id,
            user_role=test_user.role
        )
        
        # Get history
        history = await service.get_job_status_history(test_job.id, limit=10)
        
        assert len(history) == 1
        assert history[0]["from_status"] == "open"
        assert history[0]["to_status"] == "on_hold"
        assert history[0]["reason"] == "Test reason"
    
    @pytest.mark.asyncio
    async def test_dashboard_with_filters(self, db_session, test_user, test_job):
        """Test dashboard with filters"""
        service = JobsManagementService(db_session)
        
        # Filter by status
        result = await service.get_dashboard(
            user_id=test_user.id,
            user_role=test_user.role,
            status="open",
            page=1,
            limit=20
        )
        
        assert len(result["jobs"]) == 1
        
        # Filter by non-existent status
        result = await service.get_dashboard(
            user_id=test_user.id,
            user_role=test_user.role,
            status="closed",
            page=1,
            limit=20
        )
        
        assert len(result["jobs"]) == 0
    
    @pytest.mark.asyncio
    async def test_dashboard_search(self, db_session, test_user, test_job):
        """Test dashboard search functionality"""
        service = JobsManagementService(db_session)
        
        # Search by title
        result = await service.get_dashboard(
            user_id=test_user.id,
            user_role=test_user.role,
            search="Software",
            page=1,
            limit=20
        )
        
        assert len(result["jobs"]) == 1
        
        # Search with no results
        result = await service.get_dashboard(
            user_id=test_user.id,
            user_role=test_user.role,
            search="NonExistent",
            page=1,
            limit=20
        )
        
        assert len(result["jobs"]) == 0
    
    @pytest.mark.asyncio
    async def test_admin_only_archive(self, db_session, test_user, test_job):
        """Test that only admins can archive"""
        service = JobsManagementService(db_session)
        
        # First close the job
        await service.update_job_status(
            job_id=test_job.id,
            new_status="closed",
            reason="Filled",
            user_id=test_user.id,
            user_role="admin"
        )
        
        # Non-admin tries to archive
        with pytest.raises(ValueError, match="Only admins can archive"):
            await service.update_job_status(
                job_id=test_job.id,
                new_status="archived",
                reason="Test",
                user_id=test_user.id,
                user_role="recruiter"
            )
        
        # Admin can archive
        result = await service.update_job_status(
            job_id=test_job.id,
            new_status="archived",
            reason="Test",
            user_id=test_user.id,
            user_role="admin"
        )
        
        assert result["status"] == "archived"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
