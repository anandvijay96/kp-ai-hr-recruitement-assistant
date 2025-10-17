"""SQLAlchemy ORM models for authentication and resume management"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Text, ForeignKey, CheckConstraint, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


def generate_uuid():
    """Generate UUID as string"""
    return str(uuid.uuid4())


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    mobile = Column(String(15), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="recruiter")
    is_active = Column(Boolean, default=False, index=True)
    email_verified = Column(Boolean, default=False, index=True)
    department = Column(String(100))
    reporting_to = Column(String(36), ForeignKey("users.id"))
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    deactivated_by = Column(String(36), ForeignKey("users.id"))
    
    # New columns for Feature 10
    status = Column(String(50), default="active", index=True)
    deactivation_reason = Column(Text)
    last_activity_at = Column(DateTime(timezone=True))
    locked_until = Column(DateTime(timezone=True))
    
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'manager', 'recruiter')", name="chk_role"),
        CheckConstraint("status IN ('active', 'inactive', 'locked', 'pending_activation')", name="chk_user_status"),
    )


class PasswordHistory(Base):
    """Password history model"""
    __tablename__ = "password_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VerificationToken(Base):
    """Verification token model"""
    __tablename__ = "verification_tokens"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    token_type = Column(String(20), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("token_type IN ('email_verification', 'password_reset')", name="chk_token_type"),
    )


class UserSession(Base):
    """User session model"""
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token_hash = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, index=True)


class UserActivityLog(Base):
    """User activity log model - Enhanced for Phase 3"""
    __tablename__ = "user_activity_log"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action_type = Column(String(50), nullable=False, index=True)  # 'login', 'view_candidate', 'vet_resume', 'search', etc.
    
    # Phase 3 Enhancement: Entity tracking
    entity_type = Column(String(50), index=True)  # 'candidate', 'job', 'report', 'resume', etc.
    entity_id = Column(String(36), index=True)  # ID of the affected entity
    request_metadata = Column(JSON)  # Additional context (filters, search terms, request params)
    
    # Request metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_method = Column(String(10))  # GET, POST, PUT, DELETE
    request_path = Column(String(500))
    duration_ms = Column(Integer)  # Request duration in milliseconds
    
    # Status and error handling
    status = Column(String(20), nullable=False, index=True)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint("status IN ('success', 'failure')", name="chk_status"),
    )


class Resume(Base):
    """Resume model for storing uploaded resumes"""
    __tablename__ = "resumes"
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # File Information
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # Removed unique=True to allow re-upload after delete
    mime_type = Column(String(100), nullable=False)
    
    # Candidate Information (extracted)
    candidate_name = Column(String(200))
    candidate_email = Column(String(255), index=True)
    candidate_phone = Column(String(20))
    
    # Candidate Link (NEW)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="SET NULL"), index=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")
    job_matches = relationship("ResumeJobMatch", back_populates="resume", cascade="all, delete-orphan")
    
    # Parsed Data
    extracted_text = Column(Text)
    parsed_data = Column(JSON)  # Use JSON for SQLite, JSONB for PostgreSQL
    
    # Assessment Scores
    authenticity_score = Column(Integer)  # 0-100
    jd_match_score = Column(Integer)  # 0-100
    
    # Upload Metadata
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Nullable for system uploads
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    upload_ip = Column(String(45))
    upload_user_agent = Column(Text)
    
    # Processing Status
    status = Column(String(20), nullable=False, default="uploaded", index=True)
    processing_status = Column(String(20), default="pending", index=True)
    processing_error = Column(Text)
    processed_at = Column(DateTime(timezone=True))
    
    # Virus Scanning
    virus_scan_status = Column(String(20), default="pending", index=True)
    virus_scan_date = Column(DateTime(timezone=True))
    virus_scan_result = Column(Text)
    
    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), index=True)
    deleted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    __table_args__ = (
        CheckConstraint("file_type IN ('pdf', 'docx', 'txt')", name="chk_file_type"),
        CheckConstraint("status IN ('uploaded', 'parsing', 'parsed', 'failed', 'archived', 'deleted')", name="chk_resume_status"),
        CheckConstraint("virus_scan_status IN ('pending', 'scanning', 'clean', 'infected', 'failed')", name="chk_virus_status"),
        CheckConstraint("file_size > 0 AND file_size <= 10485760", name="chk_file_size"),
    )


class ResumeUploadHistory(Base):
    """Resume upload history for audit trail"""
    __tablename__ = "resume_upload_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    action = Column(String(50), nullable=False, index=True)
    performed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    details = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class BulkUploadSession(Base):
    """Bulk upload session tracking"""
    __tablename__ = "bulk_upload_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    total_files = Column(Integer, nullable=False)
    processed_files = Column(Integer, default=0)
    successful_uploads = Column(Integer, default=0)
    failed_uploads = Column(Integer, default=0)
    duplicate_files = Column(Integer, default=0)
    status = Column(String(20), default="in_progress", index=True)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))
    session_metadata = Column(JSON)  # Changed from 'metadata' to 'session_metadata'
    
    __table_args__ = (
        CheckConstraint("total_files > 0 AND total_files <= 50", name="chk_total_files"),
        CheckConstraint("status IN ('in_progress', 'completed', 'cancelled', 'failed')", name="chk_session_status"),
    )

class Candidate(Base):
    """Candidate model for storing candidate information"""
    __tablename__ = "candidates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    uuid = Column(String(36), unique=True, nullable=False, default=generate_uuid, index=True)
    
    # Personal Information
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50), index=True)
    linkedin_url = Column(String(500))
    linkedin_suggestions = Column(JSON)  # Array of LinkedIn profiles found during vetting for HR to select
    location = Column(String(255))
    professional_summary = Column(Text)  # Professional summary/objective
    
    # Metadata
    source = Column(String(50), default="upload")
    status = Column(String(50), default="new", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Soft delete fields
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(255), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    
    # Relationships
    resumes = relationship("Resume", back_populates="candidate", foreign_keys="Resume.candidate_id")
    skills = relationship("CandidateSkill", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    work_experience = relationship("WorkExperience", back_populates="candidate", cascade="all, delete-orphan")  # Add alias
    experience = relationship("WorkExperience", back_populates="candidate", cascade="all, delete-orphan", overlaps="work_experience")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="candidate", cascade="all, delete-orphan")
    ratings = relationship("CandidateRating", back_populates="candidate", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('new', 'screened', 'interviewed', 'offered', 'hired', 'rejected', 'archived')", name="chk_candidate_status"),
    )


class Education(Base):
    """Education records for candidates"""
    __tablename__ = "education"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    degree = Column(String(255))
    field = Column(String(255))
    institution = Column(String(255))
    location = Column(String(255))
    start_date = Column(String(20))  # Store as string for flexibility (YYYY-MM or YYYY)
    end_date = Column(String(20))
    gpa = Column(String(10))
    
    confidence_score = Column(String(10))  # Store as string (e.g., "0.95")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    candidate = relationship("Candidate", back_populates="education")


class WorkExperience(Base):
    """Work experience records for candidates"""
    __tablename__ = "work_experience"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    company = Column(String(255))
    title = Column(String(255))
    location = Column(String(255))
    start_date = Column(String(20))
    end_date = Column(String(20))
    is_current = Column(Boolean, default=False)
    duration_months = Column(Integer)
    description = Column(Text)
    responsibilities = Column(JSON)  # Array of responsibility bullet points
    
    confidence_score = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    candidate = relationship("Candidate", back_populates="experience")


class Skill(Base):
    """Skills master table"""
    __tablename__ = "skills"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50))  # technical, soft, language
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateSkill(Base):
    """Many-to-many relationship between candidates and skills"""
    __tablename__ = "candidate_skills"
    
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    proficiency = Column(String(50))  # beginner, intermediate, expert
    confidence_score = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="skills")
    skill = relationship("Skill")


class Certification(Base):
    """Certifications for candidates"""
    __tablename__ = "certifications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    issuer = Column(String(255))
    issue_date = Column(String(20))
    expiry_date = Column(String(20))
    credential_id = Column(String(255))
    
    confidence_score = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    candidate = relationship("Candidate", back_populates="certifications")


class Project(Base):
    """Projects for candidates"""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    technologies = Column(Text)  # JSON array stored as TEXT
    start_date = Column(String(20))
    end_date = Column(String(20))
    url = Column(String(500))
    
    confidence_score = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    candidate = relationship("Candidate", back_populates="projects")


class Language(Base):
    """Languages for candidates"""
    __tablename__ = "languages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    language = Column(String(100), nullable=False)
    proficiency = Column(String(50))  # native, fluent, professional, intermediate, basic
    
    confidence_score = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    candidate = relationship("Candidate", back_populates="languages")


class DuplicateCheck(Base):
    """Duplicate detection logs"""
    __tablename__ = "duplicate_checks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"))
    
    match_type = Column(String(50))  # email, phone, name, content
    match_score = Column(String(10))  # Store as string
    matched_candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="SET NULL"))
    
    resolution = Column(String(50))  # skip, merge, force_create
    resolved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    """Job requisition model"""
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    uuid = Column(String(36), unique=True, nullable=False, default=generate_uuid, index=True)
    
    # Basic Information
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(100), index=True)
    
    # Location
    location_city = Column(String(100))
    location_state = Column(String(100))
    location_country = Column(String(100), default='USA')
    is_remote = Column(Boolean, default=False)
    work_type = Column(String(50))  # onsite, remote, hybrid
    
    # Employment Details
    employment_type = Column(String(50))  # full_time, part_time, contract, internship
    num_openings = Column(Integer, default=1)
    
    # Salary Information
    salary_min = Column(String(20))  # Store as string for flexibility
    salary_max = Column(String(20))
    salary_currency = Column(String(10), default='USD')
    salary_period = Column(String(20), default='annual')
    
    # Job Description (Rich Text)
    description = Column(Text, nullable=False)
    responsibilities = Column(Text)  # JSON array stored as TEXT
    mandatory_requirements = Column(Text)  # JSON array stored as TEXT
    preferred_requirements = Column(Text)  # JSON array stored as TEXT
    education_requirement = Column(Text)
    certifications = Column(Text)  # JSON array stored as TEXT
    
    # Status & Workflow
    status = Column(String(50), default='draft', index=True)  # draft, open, on_hold, closed, archived
    published_at = Column(DateTime(timezone=True))
    closing_date = Column(String(20))  # Store as string (YYYY-MM-DD)
    closed_at = Column(DateTime(timezone=True))
    close_reason = Column(String(100))
    archived_at = Column(DateTime(timezone=True), index=True)  # NEW: For archival tracking
    application_deadline = Column(DateTime(timezone=True), index=True)  # NEW: Auto-close deadline
    
    # Analytics
    view_count = Column(Integer, default=0)  # NEW: Track job views
    
    # Metadata
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Template Reference
    template_id = Column(String(36), ForeignKey("job_templates.id", ondelete="SET NULL"))
    cloned_from_job_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"))
    
    # Search Optimization
    search_text = Column(Text)
    
    # Relationships
    resume_matches = relationship("ResumeJobMatch", back_populates="job", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("work_type IN ('onsite', 'remote', 'hybrid')", name="chk_work_type"),
        CheckConstraint("employment_type IN ('full_time', 'part_time', 'contract', 'internship')", name="chk_employment_type"),
        CheckConstraint("status IN ('draft', 'open', 'on_hold', 'closed')", name="chk_job_status"),
        CheckConstraint("num_openings > 0", name="chk_num_openings"),
    )


class JobSkill(Base):
    """Many-to-many relationship between jobs and skills"""
    __tablename__ = "job_skills"
    
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    is_mandatory = Column(Boolean, default=False, index=True)
    proficiency_level = Column(String(50))  # beginner, intermediate, expert, any
    years_required = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JobRecruiter(Base):
    """Recruiter assignments for jobs"""
    __tablename__ = "job_recruiters"
    
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    is_primary = Column(Boolean, default=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    removed_at = Column(DateTime(timezone=True))
    removed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))


class JobDocument(Base):
    """Documents attached to jobs"""
    __tablename__ = "job_documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Document Type
    document_type = Column(String(50))  # job_description, offer_letter_template, other
    
    # Upload Metadata
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Audit
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    __table_args__ = (
        CheckConstraint("file_type IN ('pdf', 'docx', 'doc')", name="chk_job_doc_type"),
        CheckConstraint("file_size > 0 AND file_size <= 5242880", name="chk_job_doc_size"),  # Max 5MB
    )


class JobTemplate(Base):
    """Job templates for quick job creation"""
    __tablename__ = "job_templates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    category = Column(String(100), index=True)
    
    # Template Content
    title_template = Column(String(255))
    description_template = Column(Text)
    responsibilities_template = Column(Text)  # JSON array
    mandatory_requirements_template = Column(Text)  # JSON array
    preferred_requirements_template = Column(Text)  # JSON array
    education_requirement_template = Column(Text)
    
    # Default Values
    default_work_type = Column(String(50))
    default_employment_type = Column(String(50))
    default_num_openings = Column(Integer, default=1)
    default_skills = Column(Text)  # JSON array of skill configs
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class JobStatusHistory(Base):
    """Job status change history"""
    __tablename__ = "job_status_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    from_status = Column(String(50))
    to_status = Column(String(50), nullable=False)
    reason = Column(Text)
    
    changed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class JobAnalytics(Base):
    """Job analytics - daily aggregated metrics"""
    __tablename__ = "job_analytics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(20), nullable=False)  # Store as YYYY-MM-DD string
    
    # Funnel Metrics
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    shortlist_count = Column(Integer, default=0)
    interview_count = Column(Integer, default=0)
    offer_count = Column(Integer, default=0)
    hire_count = Column(Integer, default=0)
    
    # Quality Metrics
    avg_match_score = Column(String(10))  # Store as string for flexibility
    median_match_score = Column(String(10))
    
    # Time Metrics (in hours/days)
    time_to_fill = Column(Integer)
    time_to_first_application = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class JobExternalPosting(Base):
    """External job portal postings (LinkedIn, Naukri, Indeed)"""
    __tablename__ = "job_external_postings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    portal = Column(String(50), nullable=False, index=True)  # 'linkedin', 'naukri', 'indeed'
    external_job_id = Column(String(255))
    status = Column(String(50), nullable=False, index=True)  # 'pending', 'posted', 'failed', 'expired'
    posted_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    portal_metadata = Column(Text)  # JSON string for portal-specific data (renamed from 'metadata' to avoid SQLAlchemy conflict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class JobAuditLog(Base):
    """Immutable audit trail for job modifications"""
    __tablename__ = "job_audit_log"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # 'create', 'update', 'status_change', 'delete', 'bulk_update'
    entity_type = Column(String(50), nullable=False)  # 'job', 'job_status', 'external_posting'
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    checksum = Column(String(64))  # SHA-256 hash for tamper detection


class BulkOperation(Base):
    """Bulk operations on multiple jobs"""
    __tablename__ = "bulk_operations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    operation_type = Column(String(50), nullable=False)  # 'status_update', 'archive', 'update_deadline', 'assign_recruiter'
    job_ids = Column(Text, nullable=False)  # JSON array of job IDs
    parameters = Column(Text, nullable=False)  # JSON object with operation parameters
    status = Column(String(50), nullable=False, index=True)  # 'pending', 'processing', 'completed', 'failed', 'partial'
    total_count = Column(Integer, nullable=False)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    error_details = Column(Text)  # JSON array of errors
    initiated_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# ============================================================================
# FEATURE 10: USER MANAGEMENT TABLES
# ============================================================================

class UserRole(Base):
    """User roles with permissions"""
    __tablename__ = "user_roles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    permissions = Column(JSON, nullable=False, default=[])
    is_system_role = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserPermission(Base):
    """Custom permission overrides for users"""
    __tablename__ = "user_permissions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(String(100), nullable=False, index=True)
    granted = Column(Boolean, default=True)
    granted_by = Column(String(36), ForeignKey("users.id"))
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    reason = Column(Text)


class UserAuditLog(Base):
    """Audit trail for user management actions"""
    __tablename__ = "user_audit_log"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    target_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    old_values = Column(JSON)
    new_values = Column(JSON)
    performed_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    checksum = Column(String(64))


class BulkUserOperation(Base):
    """Bulk operations on multiple users"""
    __tablename__ = "bulk_user_operations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    operation_type = Column(String(50), nullable=False, index=True)
    user_ids = Column(Text, nullable=False)  # JSON array
    parameters = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    total_count = Column(Integer, nullable=False)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    error_details = Column(JSON)
    initiated_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ResumeJobMatch(Base):
    """Resume-Job matching results"""
    __tablename__ = "resume_job_matches"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Integer, nullable=False, index=True)
    skill_score = Column(Integer)
    experience_score = Column(Integer)
    education_score = Column(Integer)
    matched_skills = Column(JSON)  # Changed from ARRAY(String) for SQLite compatibility
    missing_skills = Column(JSON)  # Changed from ARRAY(String) for SQLite compatibility
    match_details = Column(JSON)   # Changed from JSONB for SQLite compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    resume = relationship("Resume", back_populates="job_matches")
    job = relationship("Job", back_populates="resume_matches")
    
    __table_args__ = (
        CheckConstraint("match_score >= 0 AND match_score <= 100", name="check_match_score_range"),
        CheckConstraint("skill_score >= 0 AND skill_score <= 100", name="check_skill_score_range"),
        CheckConstraint("experience_score >= 0 AND experience_score <= 100", name="check_experience_score_range"),
        CheckConstraint("education_score >= 0 AND education_score <= 100", name="check_education_score_range"),
    )


# ============================================================================
# PHASE 3: INTERNAL HR FEATURES - ACTIVITY TRACKING & WORKFLOW
# ============================================================================

class UserDailyStats(Base):
    """Daily aggregated user activity statistics"""
    __tablename__ = "user_daily_stats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Activity Counts
    logins_count = Column(Integer, default=0)
    resumes_vetted = Column(Integer, default=0)
    candidates_viewed = Column(Integer, default=0)
    candidates_created = Column(Integer, default=0)
    candidates_updated = Column(Integer, default=0)
    searches_performed = Column(Integer, default=0)
    reports_generated = Column(Integer, default=0)
    jobs_created = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    interviews_scheduled = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    
    # Session Metrics
    total_session_time = Column(Integer, default=0)  # in seconds
    avg_session_duration = Column(Integer, default=0)  # in seconds
    total_actions = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        # Unique constraint: one record per user per day
        CheckConstraint("logins_count >= 0", name="chk_daily_logins_positive"),
        CheckConstraint("total_session_time >= 0", name="chk_daily_session_time_positive"),
    )


class UserWeeklyStats(Base):
    """Weekly aggregated user activity statistics"""
    __tablename__ = "user_weekly_stats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    week_number = Column(Integer, nullable=False, index=True)  # ISO week number (1-53)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    
    # Aggregated Activity Counts
    logins_count = Column(Integer, default=0)
    resumes_vetted = Column(Integer, default=0)
    candidates_viewed = Column(Integer, default=0)
    candidates_created = Column(Integer, default=0)
    searches_performed = Column(Integer, default=0)
    reports_generated = Column(Integer, default=0)
    jobs_created = Column(Integer, default=0)
    interviews_scheduled = Column(Integer, default=0)
    
    # Performance Metrics
    total_session_time = Column(Integer, default=0)
    avg_daily_actions = Column(Integer, default=0)
    productivity_score = Column(Integer, default=0)  # 0-100
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("week_number >= 1 AND week_number <= 53", name="chk_week_number_range"),
        CheckConstraint("productivity_score >= 0 AND productivity_score <= 100", name="chk_productivity_score_range"),
    )


class UserMonthlyStats(Base):
    """Monthly aggregated user activity statistics"""
    __tablename__ = "user_monthly_stats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12
    
    # Aggregated Activity Counts
    logins_count = Column(Integer, default=0)
    resumes_vetted = Column(Integer, default=0)
    candidates_viewed = Column(Integer, default=0)
    candidates_created = Column(Integer, default=0)
    searches_performed = Column(Integer, default=0)
    reports_generated = Column(Integer, default=0)
    jobs_created = Column(Integer, default=0)
    interviews_scheduled = Column(Integer, default=0)
    
    # Performance Metrics
    total_session_time = Column(Integer, default=0)
    avg_daily_actions = Column(Integer, default=0)
    productivity_score = Column(Integer, default=0)  # 0-100
    quality_score = Column(Integer, default=0)  # 0-100 (based on decision accuracy)
    
    # Rankings (optional)
    team_rank = Column(Integer)  # Ranking within team
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("month >= 1 AND month <= 12", name="chk_month_range"),
        CheckConstraint("productivity_score >= 0 AND productivity_score <= 100", name="chk_monthly_productivity_score_range"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 100", name="chk_quality_score_range"),
    )


class Interview(Base):
    """Interview scheduling and management"""
    __tablename__ = "interviews"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)  # Optional - not all interviews are job-specific
    
    # Scheduling Information
    scheduled_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    interviewer_ids = Column(JSON)  # Array of user IDs
    scheduled_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)
    timezone = Column(String(50), default='UTC')
    
    # Interview Details
    interview_type = Column(String(50), nullable=False, index=True)  # 'phone', 'video', 'in_person', 'technical', 'hr_round'
    interview_round = Column(Integer, default=1)  # 1st round, 2nd round, etc.
    location = Column(String(500))  # Physical location or meeting link
    meeting_link = Column(String(500))  # Video call URL
    meeting_id = Column(String(100))  # Meeting ID for video platforms
    meeting_password = Column(String(100))  # Meeting password if applicable
    
    # Status Management
    status = Column(String(50), default='scheduled', index=True)  # scheduled, confirmed, completed, cancelled, no_show, rescheduled
    
    # Notifications
    reminder_sent = Column(Boolean, default=False)
    confirmation_sent = Column(Boolean, default=False)
    
    # Interview Notes and Results
    notes = Column(Text)  # Interviewer's notes
    feedback = Column(Text)  # Structured feedback
    rating = Column(Integer)  # 1-5 rating
    recommendation = Column(String(50))  # 'hire', 'reject', 'proceed_next_round', 'hold'
    
    # Rescheduling
    original_datetime = Column(DateTime(timezone=True))  # If rescheduled
    reschedule_reason = Column(Text)
    rescheduled_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    reschedule_count = Column(Integer, default=0)
    
    # Cancellation
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    cancellation_reason = Column(Text)
    
    # Completion
    completed_at = Column(DateTime(timezone=True))
    completed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    candidate = relationship("Candidate", foreign_keys=[candidate_id])
    job = relationship("Job", foreign_keys=[job_id])
    
    __table_args__ = (
        CheckConstraint("interview_type IN ('phone', 'video', 'in_person', 'technical', 'hr_round', 'panel', 'behavioral')", name="chk_interview_type"),
        CheckConstraint("status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show', 'rescheduled')", name="chk_interview_status"),
        CheckConstraint("duration_minutes > 0 AND duration_minutes <= 480", name="chk_duration_range"),
        CheckConstraint("rating >= 1 AND rating <= 5 OR rating IS NULL", name="chk_interview_rating_range"),
        CheckConstraint("interview_round >= 1", name="chk_interview_round_positive"),
        CheckConstraint("reschedule_count >= 0", name="chk_reschedule_count_positive"),
    )


class CandidateStatusHistory(Base):
    """Candidate status change history for workflow tracking"""
    __tablename__ = "candidate_status_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status Change
    from_status = Column(String(50), index=True)
    to_status = Column(String(50), nullable=False, index=True)
    
    # Change Details
    changed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    change_reason = Column(Text)
    notes = Column(Text)
    
    # Related Entities
    related_job_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"))
    related_interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="SET NULL"))
    
    # Metadata
    activity_metadata = Column(JSON)  # Additional context
    
    # Timestamp
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    candidate = relationship("Candidate", foreign_keys=[candidate_id])
    user = relationship("User", foreign_keys=[changed_by])
    
    __table_args__ = (
        CheckConstraint("to_status IN ('new', 'screened', 'interviewed', 'offered', 'hired', 'rejected', 'archived')", name="chk_status_history_to_status"),
    )


class CandidateRating(Base):
    """Manual ratings for candidates by recruiters"""
    __tablename__ = "candidate_ratings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    # Rating categories (1-5 stars each)
    technical_skills = Column(Integer)  # 1-5
    communication = Column(Integer)  # 1-5
    culture_fit = Column(Integer)  # 1-5
    experience_level = Column(Integer)  # 1-5
    overall_rating = Column(Integer)  # 1-5 (can be calculated average or manual)
    
    # Additional feedback
    comments = Column(Text)
    strengths = Column(Text)  # What recruiter liked
    concerns = Column(Text)  # What recruiter is concerned about
    
    # Recommendation
    recommendation = Column(String(20))  # 'highly_recommended', 'recommended', 'maybe', 'not_recommended'
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="ratings")
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("technical_skills >= 1 AND technical_skills <= 5", name="check_technical_skills_range"),
        CheckConstraint("communication >= 1 AND communication <= 5", name="check_communication_range"),
        CheckConstraint("culture_fit >= 1 AND culture_fit <= 5", name="check_culture_fit_range"),
        CheckConstraint("experience_level >= 1 AND experience_level <= 5", name="check_experience_level_range"),
        CheckConstraint("overall_rating >= 1 AND overall_rating <= 5", name="check_overall_rating_range"),
        CheckConstraint("recommendation IN ('highly_recommended', 'recommended', 'maybe', 'not_recommended')", name="check_recommendation_values"),
    )
