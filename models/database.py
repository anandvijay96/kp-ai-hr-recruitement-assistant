"""SQLAlchemy ORM models for authentication and resume management"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Text, ForeignKey, CheckConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    """User activity log model"""
    __tablename__ = "user_activity_log"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action_type = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
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
    
    # Client Link (Feature 11)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    
    # Parsed Data
    extracted_text = Column(Text)
    parsed_data = Column(JSON)  # Use JSON for SQLite, JSONB for PostgreSQL
    
    # Upload Metadata
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
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
    location = Column(String(255))
    
    # Metadata
    source = Column(String(50), default="upload")
    status = Column(String(50), default="new", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Relationships
    education = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    experience = relationship("WorkExperience", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    
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
    
    # Client Reference (Feature 11)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    
    # Search Optimization
    search_text = Column(Text)
    
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


# ============================================================================
# FEATURE 11: CLIENT MANAGEMENT TABLES
# ============================================================================

class Client(Base):
    """Client organization model"""
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), index=True)
    website = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    logo_url = Column(String(500))
    status = Column(String(50), default='active', nullable=False, index=True)
    account_manager_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    deactivation_reason = Column(Text)
    
    # Relationships
    account_manager = relationship("User", foreign_keys=[account_manager_id])
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'on-hold', 'archived')", name="chk_client_status"),
    )


class ClientContact(Base):
    """Client contact persons"""
    __tablename__ = "client_contacts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    title = Column(String(100))
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    mobile = Column(String(50))
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ClientCommunication(Base):
    """Client communication tracking"""
    __tablename__ = "client_communications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    communication_type = Column(String(50), nullable=False, index=True)
    subject = Column(String(500))
    notes = Column(Text)
    communication_date = Column(DateTime(timezone=True), nullable=False, index=True)
    participants = Column(JSON)
    job_reference_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"))
    logged_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    is_important = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    attachments = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("communication_type IN ('meeting', 'phone_call', 'email', 'video_call', 'contract_signed')", name="chk_comm_type"),
    )


class ClientFeedback(Base):
    """Client performance feedback"""
    __tablename__ = "client_feedback"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback_period = Column(String(20))
    feedback_date = Column(Date, nullable=False, index=True)
    responsiveness_rating = Column(Integer, nullable=False)
    communication_rating = Column(Integer, nullable=False)
    requirements_clarity_rating = Column(Integer, nullable=False)
    decision_speed_rating = Column(Integer, nullable=False)
    overall_satisfaction = Column(Integer, nullable=False)
    written_feedback = Column(Text)
    submitted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    finalized_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    is_finalized = Column(Boolean, default=False)
    finalized_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("responsiveness_rating BETWEEN 1 AND 5", name="chk_responsiveness_rating"),
        CheckConstraint("communication_rating BETWEEN 1 AND 5", name="chk_communication_rating"),
        CheckConstraint("requirements_clarity_rating BETWEEN 1 AND 5", name="chk_requirements_clarity_rating"),
        CheckConstraint("decision_speed_rating BETWEEN 1 AND 5", name="chk_decision_speed_rating"),
        CheckConstraint("overall_satisfaction BETWEEN 1 AND 5", name="chk_overall_satisfaction"),
    )


class ClientJobAssignment(Base):
    """Job assignments to clients"""
    __tablename__ = "client_job_assignments"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    unassigned_at = Column(DateTime(timezone=True))
    unassigned_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    is_active = Column(Boolean, default=True, index=True)


class ClientAnalytics(Base):
    """Daily aggregated client analytics"""
    __tablename__ = "client_analytics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    active_jobs_count = Column(Integer, default=0)
    total_candidates_count = Column(Integer, default=0)
    screened_count = Column(Integer, default=0)
    shortlisted_count = Column(Integer, default=0)
    interviewed_count = Column(Integer, default=0)
    hired_count = Column(Integer, default=0)
    avg_time_to_fill_days = Column(Integer)
    avg_candidate_quality_score = Column(String(10))
    revenue_generated = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ============================================================================
# FEATURE 12: VENDOR MANAGEMENT TABLES
# ============================================================================

class Vendor(Base):
    """Vendor/supplier model"""
    __tablename__ = "vendors"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    service_category = Column(String(100), nullable=False, index=True)
    contact_person = Column(String(255))
    contact_email = Column(String(255), nullable=False, index=True)
    contact_phone = Column(String(50))
    alternate_contact = Column(String(255))
    website = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    tax_id = Column(String(100))
    logo_url = Column(String(500))
    status = Column(String(50), nullable=False, default='active', index=True)
    overall_rating = Column(String(10))  # Store as string for decimal precision
    total_contracts = Column(Integer, default=0)
    active_contracts = Column(Integer, default=0)
    vendor_manager_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    deactivation_reason = Column(Text)
    last_evaluation_date = Column(Date)
    compliance_status = Column(String(50), default='pending', index=True)
    
    # Relationships
    vendor_manager = relationship("User", foreign_keys=[vendor_manager_id])
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'on-hold', 'blacklisted')", name="chk_vendor_status"),
        CheckConstraint("compliance_status IN ('pending', 'compliant', 'non_compliant', 'under_review')", name="chk_compliance_status"),
    )


class VendorContract(Base):
    """Vendor contracts"""
    __tablename__ = "vendor_contracts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_number = Column(String(100), unique=True, nullable=False, index=True)
    contract_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    contract_value = Column(String(20))  # Store as string for decimal precision
    currency = Column(String(10), default='USD')
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    payment_terms = Column(Text)
    renewal_terms = Column(Text)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255))
    file_size = Column(Integer)
    version = Column(Integer, default=1)
    status = Column(String(50), nullable=False, default='draft', index=True)
    approval_status = Column(String(50), default='pending', index=True)
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(DateTime(timezone=True))
    termination_date = Column(Date)
    termination_reason = Column(Text)
    auto_renew = Column(Boolean, default=False)
    renewal_notice_days = Column(Integer, default=90)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    parent_contract_id = Column(String(36), ForeignKey("vendor_contracts.id", ondelete="SET NULL"))
    
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'pending_approval', 'approved', 'active', 'expired', 'terminated')", name="chk_contract_status"),
        CheckConstraint("approval_status IN ('pending', 'approved', 'rejected')", name="chk_approval_status"),
    )


class VendorPerformanceReview(Base):
    """Vendor performance reviews"""
    __tablename__ = "vendor_performance_reviews"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    review_period = Column(String(50), nullable=False)
    review_date = Column(Date, nullable=False, index=True)
    review_type = Column(String(50), nullable=False)
    service_quality_rating = Column(Integer, nullable=False)
    timeliness_rating = Column(Integer, nullable=False)
    communication_rating = Column(Integer, nullable=False)
    cost_effectiveness_rating = Column(Integer, nullable=False)
    compliance_rating = Column(Integer, nullable=False)
    overall_rating = Column(String(10), nullable=False)  # Store as string for decimal precision
    strengths = Column(Text)
    areas_for_improvement = Column(Text)
    recommendations = Column(Text)
    written_feedback = Column(Text)
    status = Column(String(50), default='draft', index=True)
    finalized_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    finalized_at = Column(DateTime(timezone=True))
    reviewed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("service_quality_rating BETWEEN 1 AND 5", name="chk_service_quality_rating"),
        CheckConstraint("timeliness_rating BETWEEN 1 AND 5", name="chk_timeliness_rating"),
        CheckConstraint("communication_rating BETWEEN 1 AND 5", name="chk_vendor_communication_rating"),
        CheckConstraint("cost_effectiveness_rating BETWEEN 1 AND 5", name="chk_cost_effectiveness_rating"),
        CheckConstraint("compliance_rating BETWEEN 1 AND 5", name="chk_vendor_compliance_rating"),
        CheckConstraint("status IN ('draft', 'finalized', 'archived')", name="chk_review_status"),
    )


class VendorComplianceDocument(Base):
    """Vendor compliance documents"""
    __tablename__ = "vendor_compliance_documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False, index=True)
    document_name = Column(String(255), nullable=False)
    document_number = Column(String(100))
    issue_date = Column(Date)
    expiry_date = Column(Date, index=True)
    issuing_authority = Column(String(255))
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255))
    file_size = Column(Integer)
    status = Column(String(50), nullable=False, default='valid', index=True)
    verification_status = Column(String(50), default='pending', index=True)
    verified_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    verified_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    version = Column(Integer, default=1)
    parent_document_id = Column(String(36), ForeignKey("vendor_compliance_documents.id", ondelete="SET NULL"))
    
    __table_args__ = (
        CheckConstraint("status IN ('valid', 'expiring_soon', 'expired', 'pending_review', 'rejected')", name="chk_document_status"),
        CheckConstraint("verification_status IN ('pending', 'verified', 'rejected', 'expired')", name="chk_verification_status"),
    )


class VendorCommunication(Base):
    """Vendor communications log"""
    __tablename__ = "vendor_communications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    communication_type = Column(String(50), nullable=False, index=True)
    communication_date = Column(DateTime(timezone=True), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    details = Column(Text)
    attendees = Column(Text)  # JSON array
    outcome = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_notes = Column(Text)
    tags = Column(String(255))
    attachment_urls = Column(Text)  # JSON array
    is_important = Column(Boolean, default=False, index=True)
    logged_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("communication_type IN ('meeting', 'phone_call', 'email', 'video_call', 'site_visit', 'other')", name="chk_vendor_comm_type"),
    )


class VendorNotification(Base):
    """Vendor-related notifications"""
    __tablename__ = "vendor_notifications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(100), nullable=False, index=True)
    priority = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_required = Column(Text)
    deadline = Column(Date)
    recipient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True))
    is_actioned = Column(Boolean, default=False)
    actioned_at = Column(DateTime(timezone=True))
    related_entity_type = Column(String(50))
    related_entity_id = Column(String(36))
    sent_via_email = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name="chk_notification_priority"),
        CheckConstraint("notification_type IN ('contract_expiry', 'document_expiry', 'review_due', 'compliance_alert', 'general')", name="chk_notification_type"),
    )


class VendorJobAssignment(Base):
    """Job assignments to vendors"""
    __tablename__ = "vendor_job_assignments"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(String(36), ForeignKey("vendor_contracts.id", ondelete="SET NULL"))
    assignment_date = Column(Date, nullable=False, index=True)
    status = Column(String(50), default='active', index=True)
    fee_structure = Column(String(100))
    fee_amount = Column(String(20))  # Store as string for decimal precision
    candidates_submitted = Column(Integer, default=0)
    candidates_hired = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'completed', 'cancelled')", name="chk_assignment_status"),
    )


class VendorAnalytics(Base):
    """Daily aggregated vendor analytics"""
    __tablename__ = "vendor_analytics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_jobs_assigned = Column(Integer, default=0)
    active_jobs = Column(Integer, default=0)
    candidates_submitted = Column(Integer, default=0)
    candidates_interviewed = Column(Integer, default=0)
    candidates_hired = Column(Integer, default=0)
    total_revenue = Column(String(20), default='0')  # Store as string for decimal precision
    average_rating = Column(String(10))
    response_time_hours = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
