"""Pydantic schemas for job management"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class WorkType(str, Enum):
    """Work type enumeration"""
    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"


class EmploymentType(str, Enum):
    """Employment type enumeration"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class JobStatus(str, Enum):
    """Job status enumeration"""
    DRAFT = "draft"
    OPEN = "open"
    ON_HOLD = "on_hold"
    CLOSED = "closed"


class CloseReason(str, Enum):
    """Job close reason enumeration"""
    FILLED = "filled"
    CANCELLED = "cancelled"
    BUDGET_CUT = "budget_cut"
    POSITION_ELIMINATED = "position_eliminated"


class ProficiencyLevel(str, Enum):
    """Skill proficiency level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    ANY = "any"


# ============================================================================
# NESTED MODELS
# ============================================================================

class LocationModel(BaseModel):
    """Location information"""
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"
    is_remote: bool = False


class SalaryRangeModel(BaseModel):
    """Salary range information"""
    min: Optional[float] = Field(None, ge=0)
    max: Optional[float] = Field(None, ge=0)
    currency: str = "USD"
    period: str = "annual"
    
    @validator('max')
    def validate_salary_range(cls, v, values):
        """Validate that max salary is greater than min"""
        if v and 'min' in values and values['min']:
            if v < values['min']:
                raise ValueError("Maximum salary cannot be less than minimum salary")
        return v


class JobSkillModel(BaseModel):
    """Job skill information"""
    skill_id: Optional[str] = None
    name: str
    is_mandatory: bool = False
    proficiency_level: ProficiencyLevel = ProficiencyLevel.ANY
    years_required: Optional[int] = Field(None, ge=0)


class RequirementsModel(BaseModel):
    """Job requirements"""
    mandatory: List[str] = []
    preferred: List[str] = []


class RecruiterAssignmentModel(BaseModel):
    """Recruiter assignment"""
    user_id: str
    is_primary: bool = False


# ============================================================================
# REQUEST MODELS
# ============================================================================

class JobCreateRequest(BaseModel):
    """Request model for creating a new job"""
    
    # Basic Information
    title: str = Field(..., min_length=3, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    
    # Location
    location: LocationModel
    work_type: WorkType
    
    # Employment
    employment_type: EmploymentType
    num_openings: int = Field(1, ge=1, le=100)
    
    # Salary (Optional)
    salary_range: Optional[SalaryRangeModel] = None
    
    # Description
    description: str = Field(..., min_length=50, max_length=50000)
    responsibilities: List[str] = []
    requirements: RequirementsModel = RequirementsModel()
    education_requirement: Optional[str] = None
    certifications: List[str] = []
    
    # Skills
    skills: List[JobSkillModel] = []
    
    # Dates
    closing_date: Optional[date] = None
    
    # Recruiters
    assigned_recruiters: List[RecruiterAssignmentModel] = []
    
    # Status
    status: JobStatus = JobStatus.DRAFT
    
    # Template
    template_id: Optional[str] = None
    
    @validator('closing_date')
    def validate_closing_date(cls, v):
        """Validate that closing date is not in the past"""
        if v and v < date.today():
            raise ValueError("Closing date cannot be in the past")
        return v


class JobUpdateRequest(BaseModel):
    """Request model for updating a job (partial updates allowed)"""
    
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    department: Optional[str] = None
    location: Optional[LocationModel] = None
    work_type: Optional[WorkType] = None
    employment_type: Optional[EmploymentType] = None
    num_openings: Optional[int] = Field(None, ge=1, le=100)
    salary_range: Optional[SalaryRangeModel] = None
    description: Optional[str] = Field(None, min_length=50, max_length=50000)
    responsibilities: Optional[List[str]] = None
    requirements: Optional[RequirementsModel] = None
    education_requirement: Optional[str] = None
    certifications: Optional[List[str]] = None
    skills: Optional[List[JobSkillModel]] = None
    closing_date: Optional[date] = None


class JobPublishRequest(BaseModel):
    """Request model for publishing a job"""
    send_notifications: bool = True
    notify_recruiters: bool = True


class JobCloseRequest(BaseModel):
    """Request model for closing a job"""
    close_reason: CloseReason
    notes: Optional[str] = None


class JobCloneRequest(BaseModel):
    """Request model for cloning a job"""
    new_title: Optional[str] = None
    modify_fields: Optional[dict] = None


class AssignRecruitersRequest(BaseModel):
    """Request model for assigning recruiters to a job"""
    recruiters: List[RecruiterAssignmentModel]
    send_notifications: bool = True


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class JobSummaryResponse(BaseModel):
    """Summary response for job listings"""
    
    id: str
    uuid: str
    title: str
    department: Optional[str]
    location_city: Optional[str]
    location_state: Optional[str]
    work_type: str
    employment_type: str
    num_openings: int
    status: str
    published_at: Optional[datetime]
    closing_date: Optional[str]
    created_at: datetime
    
    # Counts
    total_applications: int = 0
    assigned_recruiters_count: int = 0
    
    class Config:
        from_attributes = True


class JobDetailResponse(BaseModel):
    """Detailed response for single job"""
    
    id: str
    uuid: str
    title: str
    department: Optional[str]
    
    # Location
    location_city: Optional[str]
    location_state: Optional[str]
    location_country: str
    is_remote: bool
    work_type: str
    
    # Employment
    employment_type: str
    num_openings: int
    
    # Salary
    salary_min: Optional[str]
    salary_max: Optional[str]
    salary_currency: str
    salary_period: str
    
    # Description
    description: str
    responsibilities: List[str]
    mandatory_requirements: List[str]
    preferred_requirements: List[str]
    education_requirement: Optional[str]
    certifications: List[str]
    
    # Skills
    skills: List[dict]
    
    # Status
    status: str
    published_at: Optional[datetime]
    closing_date: Optional[str]
    closed_at: Optional[datetime]
    close_reason: Optional[str]
    
    # Metadata
    created_by: dict
    created_at: datetime
    updated_at: datetime
    
    # Recruiters
    assigned_recruiters: List[dict]
    
    # Documents
    documents: List[dict]
    
    # Statistics
    total_applications: int = 0
    
    class Config:
        from_attributes = True


class PaginatedJobsResponse(BaseModel):
    """Paginated response for job listings"""
    
    success: bool = True
    data: dict = {
        "jobs": [],
        "total": 0,
        "page": 1,
        "limit": 20,
        "total_pages": 0
    }
    message: Optional[str] = None


class StandardJobResponse(BaseModel):
    """Standard API response wrapper"""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None
