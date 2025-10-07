import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from core.database import Base
from models.db import Candidate, Resume, Education, WorkExperience, Skill, candidate_skills


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestCandidateModel:
    """Test Candidate model operations"""
    
    def test_create_candidate(self, test_db: Session):
        """Test creating a candidate"""
        candidate = Candidate(
            full_name="John Doe",
            email="john.doe@example.com",
            phone_number="+1234567890",
            linkedin_url="https://linkedin.com/in/johndoe"
        )
        test_db.add(candidate)
        test_db.commit()
        test_db.refresh(candidate)
        
        assert candidate.id is not None
        assert candidate.full_name == "John Doe"
        assert candidate.email == "john.doe@example.com"
        assert candidate.created_at is not None
    
    def test_candidate_email_unique(self, test_db: Session):
        """Test that email must be unique"""
        candidate1 = Candidate(
            full_name="John Doe",
            email="john@example.com"
        )
        test_db.add(candidate1)
        test_db.commit()
        
        # Try to add another with same email
        candidate2 = Candidate(
            full_name="Jane Doe",
            email="john@example.com"
        )
        test_db.add(candidate2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db.commit()
    
    def test_candidate_relationships(self, test_db: Session):
        """Test candidate relationships with other models"""
        candidate = Candidate(
            full_name="John Doe",
            email="john@example.com"
        )
        test_db.add(candidate)
        test_db.commit()
        test_db.refresh(candidate)
        
        # Add education
        education = Education(
            candidate_id=candidate.id,
            degree="Bachelor of Science",
            institution="MIT"
        )
        test_db.add(education)
        
        # Add work experience
        experience = WorkExperience(
            candidate_id=candidate.id,
            company="Google",
            job_title="Software Engineer"
        )
        test_db.add(experience)
        
        test_db.commit()
        test_db.refresh(candidate)
        
        assert len(candidate.education) == 1
        assert len(candidate.work_experience) == 1
        assert candidate.education[0].degree == "Bachelor of Science"
        assert candidate.work_experience[0].company == "Google"


class TestResumeModel:
    """Test Resume model operations"""
    
    def test_create_resume(self, test_db: Session):
        """Test creating a resume"""
        resume = Resume(
            file_name="resume.pdf",
            file_path="/uploads/resume.pdf",
            file_hash="abc123",
            upload_status="pending"
        )
        test_db.add(resume)
        test_db.commit()
        test_db.refresh(resume)
        
        assert resume.id is not None
        assert resume.file_name == "resume.pdf"
        assert resume.upload_status == "pending"
        assert resume.uploaded_at is not None
    
    def test_resume_file_hash_unique(self, test_db: Session):
        """Test that file hash must be unique"""
        resume1 = Resume(
            file_name="resume1.pdf",
            file_path="/uploads/resume1.pdf",
            file_hash="hash123"
        )
        test_db.add(resume1)
        test_db.commit()
        
        # Try to add another with same hash
        resume2 = Resume(
            file_name="resume2.pdf",
            file_path="/uploads/resume2.pdf",
            file_hash="hash123"
        )
        test_db.add(resume2)
        
        with pytest.raises(Exception):
            test_db.commit()
    
    def test_resume_candidate_relationship(self, test_db: Session):
        """Test resume-candidate relationship"""
        candidate = Candidate(
            full_name="John Doe",
            email="john@example.com"
        )
        test_db.add(candidate)
        test_db.commit()
        test_db.refresh(candidate)
        
        resume = Resume(
            candidate_id=candidate.id,
            file_name="resume.pdf",
            file_path="/uploads/resume.pdf",
            file_hash="hash123"
        )
        test_db.add(resume)
        test_db.commit()
        test_db.refresh(resume)
        
        assert resume.candidate_id == candidate.id
        assert resume.candidate.full_name == "John Doe"
        assert len(candidate.resumes) == 1


class TestSkillModel:
    """Test Skill and Candidate-Skill relationship"""
    
    def test_create_skill(self, test_db: Session):
        """Test creating a skill"""
        skill = Skill(name="Python", category="Programming")
        test_db.add(skill)
        test_db.commit()
        test_db.refresh(skill)
        
        assert skill.id is not None
        assert skill.name == "Python"
        assert skill.category == "Programming"
    
    def test_skill_name_unique(self, test_db: Session):
        """Test that skill name must be unique"""
        skill1 = Skill(name="Python")
        test_db.add(skill1)
        test_db.commit()
        
        skill2 = Skill(name="Python")
        test_db.add(skill2)
        
        with pytest.raises(Exception):
            test_db.commit()
    
    def test_candidate_skill_relationship(self, test_db: Session):
        """Test many-to-many relationship between candidates and skills"""
        # Create candidate
        candidate = Candidate(
            full_name="John Doe",
            email="john@example.com"
        )
        test_db.add(candidate)
        test_db.commit()
        test_db.refresh(candidate)
        
        # Create skills
        python = Skill(name="Python")
        java = Skill(name="Java")
        test_db.add_all([python, java])
        test_db.commit()
        
        # Associate skills with candidate
        candidate.skills.append(python)
        candidate.skills.append(java)
        test_db.commit()
        test_db.refresh(candidate)
        
        assert len(candidate.skills) == 2
        assert "Python" in [s.name for s in candidate.skills]
        assert "Java" in [s.name for s in candidate.skills]


class TestEducationModel:
    """Test Education model"""
    
    def test_create_education(self, test_db: Session):
        """Test creating education record"""
        candidate = Candidate(
            full_name="John Doe",
            email="john@example.com"
        )
        test_db.add(candidate)
        test_db.commit()
        
        education = Education(
            candidate_id=candidate.id,
            degree="Master of Science",
            institution="Stanford University",
            field_of_study="Computer Science"
        )
        test_db.add(education)
        test_db.commit()
        test_db.refresh(education)
        
        assert education.id is not None
        assert education.degree == "Master of Science"
        assert education.institution == "Stanford University"


class TestWorkExperienceModel:
    """Test WorkExperience model"""
    
    def test_create_work_experience(self, test_db: Session):
        """Test creating work experience record"""
        candidate = Candidate(
            full_name="John Doe",
            email="john@example.com"
        )
        test_db.add(candidate)
        test_db.commit()
        
        experience = WorkExperience(
            candidate_id=candidate.id,
            company="Google",
            job_title="Senior Software Engineer",
            is_current=True
        )
        test_db.add(experience)
        test_db.commit()
        test_db.refresh(experience)
        
        assert experience.id is not None
        assert experience.company == "Google"
        assert experience.is_current is True
