"""Pydantic schemas for candidate management and parsed resume data"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CandidateStatus(str, Enum):
    """Candidate status enum"""
    NEW = "new"
    SCREENED = "screened"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class SkillCategory(str, Enum):
    """Skill category enum"""
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"


class Proficiency(str, Enum):
    """Skill proficiency level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


# ============================================================================
# Parsed Data Schemas (from resume extraction)
# ============================================================================

class PersonalInfo(BaseModel):
    """Personal information extracted from resume"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    confidence: Dict[str, float] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "linkedin_url": "linkedin.com/in/johndoe",
                "location": "San Francisco, CA",
                "confidence": {
                    "name": 0.98,
                    "email": 1.0,
                    "phone": 0.95
                }
            }
        }


class EducationData(BaseModel):
    """Education information extracted from resume"""
    degree: str
    field: Optional[str] = None
    institution: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    confidence: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "institution": "Stanford University",
                "location": "Stanford, CA",
                "start_date": "2015-09",
                "end_date": "2019-06",
                "gpa": "3.8",
                "confidence": 0.92
            }
        }


class WorkExperienceData(BaseModel):
    """Work experience extracted from resume"""
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "company": "Google",
                "title": "Senior Software Engineer",
                "location": "Mountain View, CA",
                "start_date": "2021-03",
                "end_date": "Present",
                "duration_months": 42,
                "description": "Led development of...",
                "achievements": ["Improved system performance by 40%"],
                "confidence": 0.95
            }
        }


class SkillData(BaseModel):
    """Skill extracted from resume"""
    name: str
    category: str = "technical"
    proficiency: Optional[str] = None
    confidence: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python",
                "category": "technical",
                "proficiency": "expert",
                "confidence": 0.98
            }
        }


class CertificationData(BaseModel):
    """Certification extracted from resume"""
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    confidence: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "AWS Certified Solutions Architect",
                "issuer": "Amazon Web Services",
                "date": "2022-06",
                "expiry_date": "2025-06",
                "credential_id": "AWS-SA-12345",
                "confidence": 0.98
            }
        }


class ParsedResumeData(BaseModel):
    """Complete parsed resume data structure"""
    personal_info: PersonalInfo
    education: List[EducationData] = Field(default_factory=list)
    experience: List[WorkExperienceData] = Field(default_factory=list)
    skills: List[SkillData] = Field(default_factory=list)
    certifications: List[CertificationData] = Field(default_factory=list)
    total_experience_months: Optional[int] = None
    summary: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "personal_info": {
                    "name": "John Doe",
                    "email": "john.doe@example.com"
                },
                "education": [],
                "experience": [],
                "skills": [],
                "certifications": [],
                "total_experience_months": 60
            }
        }


# ============================================================================
# Candidate Request/Response Schemas
# ============================================================================

class CandidateCreate(BaseModel):
    """Schema for creating a candidate"""
    full_name: str = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    source: str = "upload"
    status: CandidateStatus = CandidateStatus.NEW


class CandidateUpdate(BaseModel):
    """Schema for updating a candidate"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[CandidateStatus] = None


class EducationResponse(BaseModel):
    """Education response schema"""
    id: str
    degree: Optional[str]
    field: Optional[str]
    institution: Optional[str]
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    gpa: Optional[str]
    confidence_score: Optional[str]
    
    class Config:
        from_attributes = True


class WorkExperienceResponse(BaseModel):
    """Work experience response schema"""
    id: str
    company: Optional[str]
    title: Optional[str]
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    is_current: bool
    duration_months: Optional[int]
    description: Optional[str]
    confidence_score: Optional[str]
    
    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    """Skill response schema"""
    id: str
    name: str
    category: Optional[str]
    proficiency: Optional[str]
    confidence_score: Optional[str]
    
    class Config:
        from_attributes = True


class CertificationResponse(BaseModel):
    """Certification response schema"""
    id: str
    name: str
    issuer: Optional[str]
    issue_date: Optional[str]
    expiry_date: Optional[str]
    credential_id: Optional[str]
    confidence_score: Optional[str]
    
    class Config:
        from_attributes = True


class CandidateResponse(BaseModel):
    """Complete candidate response with all related data"""
    id: str
    uuid: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    location: Optional[str]
    source: str
    status: str
    created_at: datetime
    updated_at: datetime
    education: List[EducationResponse] = Field(default_factory=list)
    experience: List[WorkExperienceResponse] = Field(default_factory=list)
    skills: List[SkillResponse] = Field(default_factory=list)
    certifications: List[CertificationResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class CandidateListItem(BaseModel):
    """Candidate item for list view"""
    id: str
    uuid: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    status: str
    created_at: datetime
    total_experience_months: Optional[int] = None
    education_count: int = 0
    skills_count: int = 0
    
    class Config:
        from_attributes = True


class PaginatedCandidateResponse(BaseModel):
    """Paginated candidate list response"""
    success: bool
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "candidates": [],
                    "pagination": {
                        "page": 1,
                        "limit": 20,
                        "total": 150,
                        "total_pages": 8
                    }
                }
            }
        }


# ============================================================================
# Duplicate Detection Schemas
# ============================================================================

class DuplicateMatch(BaseModel):
    """Duplicate match information"""
    candidate_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    match_type: str  # email, phone, name, content
    match_score: float
    uploaded_at: Optional[datetime]
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "email": "john@example.com",
                "match_type": "email",
                "match_score": 1.0,
                "uploaded_at": "2025-09-15T10:30:00Z"
            }
        }


class DuplicateResolution(str, Enum):
    """Duplicate resolution options"""
    SKIP = "skip"
    MERGE = "merge"
    FORCE_CREATE = "force_create"


class ResolveDuplicateRequest(BaseModel):
    """Request to resolve a duplicate"""
    action: DuplicateResolution
    matched_candidate_id: Optional[str] = None


class DuplicateCheckResponse(BaseModel):
    """Response for duplicate check"""
    is_duplicate: bool
    duplicates: List[DuplicateMatch] = Field(default_factory=list)
    options: List[str] = ["skip", "merge", "force_create"]
