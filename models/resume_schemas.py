"""Pydantic models for resume upload and management"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


class ResumeStatus(str, Enum):
    """Resume processing status"""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class VirusScanStatus(str, Enum):
    """Virus scan status"""
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    FAILED = "failed"


class FileType(str, Enum):
    """Allowed file types"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


# Request Models

class ResumeUploadMetadata(BaseModel):
    """Optional metadata for resume upload"""
    candidate_name: Optional[str] = Field(None, max_length=200)
    candidate_email: Optional[str] = Field(None, max_length=255)
    candidate_phone: Optional[str] = Field(None, max_length=20)
    
    @validator('candidate_email')
    def validate_email(cls, v):
        if v and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError('Invalid email format')
        return v


class BulkUploadRequest(BaseModel):
    """Request for bulk upload session"""
    total_files: int = Field(..., ge=1, le=50)


class DuplicateHandlingOption(str, Enum):
    """Options for handling duplicate resumes"""
    SKIP = "skip"
    REPLACE = "replace"
    NEW_VERSION = "new_version"


class DuplicateHandlingRequest(BaseModel):
    """Request for handling duplicate resume"""
    file_hash: str = Field(..., min_length=64, max_length=64)
    action: DuplicateHandlingOption


# Response Models

class ResumeUploadResponse(BaseModel):
    """Response for single resume upload"""
    success: bool
    message: str
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Resume uploaded successfully",
                "data": {
                    "resume_id": "123e4567-e89b-12d3-a456-426614174000",
                    "file_name": "john_doe_resume.pdf",
                    "file_size": 2457600,
                    "file_type": "pdf",
                    "upload_date": "2025-10-03T10:30:00Z",
                    "virus_scan_status": "pending",
                    "is_duplicate": False
                }
            }
        }


class ResumeDetailResponse(BaseModel):
    """Detailed resume information"""
    id: str
    file_name: str
    original_file_name: str
    file_size: int
    file_type: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    uploaded_by: Dict[str, str]  # {id, name, email}
    upload_date: datetime
    status: str
    virus_scan_status: str
    parsed_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ResumeListItem(BaseModel):
    """Resume item in list view"""
    id: str
    file_name: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    upload_date: datetime
    uploaded_by_name: str
    status: str
    file_size: int
    virus_scan_status: str


class PaginatedResumeResponse(BaseModel):
    """Paginated list of resumes"""
    success: bool
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "resumes": [],
                    "pagination": {
                        "page": 1,
                        "limit": 20,
                        "total": 150,
                        "total_pages": 8
                    }
                }
            }
        }


class BulkUploadStatusResponse(BaseModel):
    """Bulk upload session status"""
    session_id: str
    status: str
    total_files: int
    processed: int
    successful: int
    failed: int
    duplicates: int
    progress_percentage: float
    files: List[Dict[str, Any]]


class DuplicateDetectionResponse(BaseModel):
    """Response for duplicate detection"""
    is_duplicate: bool
    existing_resume: Optional[Dict[str, Any]] = None
    options: List[str] = ["skip", "replace", "new_version"]


class VirusScanResponse(BaseModel):
    """Virus scan result"""
    resume_id: str
    scan_status: str
    scan_date: datetime
    scan_result: Optional[str] = None
    is_safe: bool
