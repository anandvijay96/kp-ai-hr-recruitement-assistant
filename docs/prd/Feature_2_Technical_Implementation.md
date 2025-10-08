# Feature 2: Resume Upload - Technical Implementation Document

**Version:** 1.0  
**Last Updated:** 2025-10-03  
**Status:** Implementation Ready  
**Related PRD:** Feature_2_Resume_Upload_PRD.md

---

## 1. DATABASE DESIGN

### 1.1 Database Schema

#### Table: `resumes`
```sql
CREATE TABLE resumes (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- File Information
    file_name VARCHAR(255) NOT NULL,
    original_file_name VARCHAR(255) NOT NULL,  -- User's original filename
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0 AND file_size <= 10485760), -- Max 10MB
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('pdf', 'docx', 'txt')),
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash for duplicate detection
    mime_type VARCHAR(100) NOT NULL,
    
    -- Candidate Information (extracted during parsing)
    candidate_name VARCHAR(200),
    candidate_email VARCHAR(255),
    candidate_phone VARCHAR(20),
    
    -- Parsed Data
    extracted_text TEXT,
    parsed_data JSONB DEFAULT '{}',  -- Skills, experience, education, etc.
    
    -- Upload Metadata
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    upload_ip VARCHAR(45),
    upload_user_agent TEXT,
    
    -- Processing Status
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded' 
        CHECK (status IN ('uploaded', 'parsing', 'parsed', 'failed', 'archived', 'deleted')),
    
    -- Virus Scanning
    virus_scan_status VARCHAR(20) DEFAULT 'pending'
        CHECK (virus_scan_status IN ('pending', 'scanning', 'clean', 'infected', 'failed')),
    virus_scan_date TIMESTAMP WITH TIME ZONE,
    virus_scan_result TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT unique_file_hash UNIQUE (file_hash)
);

-- Indexes for performance
CREATE INDEX idx_resumes_uploaded_by ON resumes(uploaded_by);
CREATE INDEX idx_resumes_upload_date ON resumes(upload_date DESC);
CREATE INDEX idx_resumes_status ON resumes(status);
CREATE INDEX idx_resumes_file_hash ON resumes(file_hash);
CREATE INDEX idx_resumes_candidate_email ON resumes(candidate_email);
CREATE INDEX idx_resumes_virus_scan_status ON resumes(virus_scan_status);
CREATE INDEX idx_resumes_deleted_at ON resumes(deleted_at) WHERE deleted_at IS NULL;

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_resumes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_resumes_updated_at
    BEFORE UPDATE ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION update_resumes_updated_at();
```

#### Table: `resume_upload_history`
```sql
CREATE TABLE resume_upload_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,  -- uploaded, updated, deleted, scanned, parsed
    performed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_upload_history_resume_id ON resume_upload_history(resume_id);
CREATE INDEX idx_upload_history_timestamp ON resume_upload_history(timestamp DESC);
CREATE INDEX idx_upload_history_action ON resume_upload_history(action);
```

#### Table: `bulk_upload_sessions`
```sql
CREATE TABLE bulk_upload_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_files INTEGER NOT NULL CHECK (total_files > 0 AND total_files <= 50),
    processed_files INTEGER DEFAULT 0,
    successful_uploads INTEGER DEFAULT 0,
    failed_uploads INTEGER DEFAULT 0,
    duplicate_files INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'cancelled', 'failed')),
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_bulk_sessions_user_id ON bulk_upload_sessions(user_id);
CREATE INDEX idx_bulk_sessions_status ON bulk_upload_sessions(status);
CREATE INDEX idx_bulk_sessions_started_at ON bulk_upload_sessions(started_at DESC);
```

#### Table: `resume_versions` (for handling duplicate uploads)
```sql
CREATE TABLE resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    
    CONSTRAINT unique_resume_version UNIQUE (original_resume_id, version_number)
);

CREATE INDEX idx_resume_versions_original_id ON resume_versions(original_resume_id);
```

### 1.2 Migration Script

```python
# migrations/versions/002_create_resume_tables.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('original_file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(10), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('candidate_name', sa.String(200)),
        sa.Column('candidate_email', sa.String(255)),
        sa.Column('candidate_phone', sa.String(20)),
        sa.Column('extracted_text', sa.Text()),
        sa.Column('parsed_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('upload_ip', sa.String(45)),
        sa.Column('upload_user_agent', sa.Text()),
        sa.Column('status', sa.String(20), nullable=False, server_default='uploaded'),
        sa.Column('virus_scan_status', sa.String(20), server_default='pending'),
        sa.Column('virus_scan_date', sa.DateTime(timezone=True)),
        sa.Column('virus_scan_result', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
    )
    
    # Create indexes
    op.create_index('idx_resumes_uploaded_by', 'resumes', ['uploaded_by'])
    op.create_index('idx_resumes_upload_date', 'resumes', ['upload_date'], postgresql_ops={'upload_date': 'DESC'})
    op.create_index('idx_resumes_status', 'resumes', ['status'])
    op.create_index('idx_resumes_file_hash', 'resumes', ['file_hash'], unique=True)
    
    # Create other tables...
    # (Similar pattern for resume_upload_history, bulk_upload_sessions, resume_versions)

def downgrade():
    op.drop_table('resume_versions')
    op.drop_table('bulk_upload_sessions')
    op.drop_table('resume_upload_history')
    op.drop_table('resumes')
```

---

## 2. API DESIGN

### 2.1 Pydantic Models

```python
# models/resume_schemas.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re

class ResumeStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"

class VirusScanStatus(str, Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    FAILED = "failed"

class FileType(str, Enum):
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
        schema_extra = {
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
    file_type: FileType
    candidate_name: Optional[str]
    candidate_email: Optional[str]
    candidate_phone: Optional[str]
    uploaded_by: Dict[str, str]  # {id, name, email}
    upload_date: datetime
    status: ResumeStatus
    virus_scan_status: VirusScanStatus
    parsed_data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class ResumeListItem(BaseModel):
    """Resume item in list view"""
    id: str
    file_name: str
    candidate_name: Optional[str]
    candidate_email: Optional[str]
    upload_date: datetime
    uploaded_by_name: str
    status: ResumeStatus
    file_size: int
    virus_scan_status: VirusScanStatus

class PaginatedResumeResponse(BaseModel):
    """Paginated list of resumes"""
    success: bool
    data: Dict[str, Any]
    
    class Config:
        schema_extra = {
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
    scan_status: VirusScanStatus
    scan_date: datetime
    scan_result: Optional[str]
    is_safe: bool
```

### 2.2 API Endpoints

```python
# api/resumes.py

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
import logging

from models.resume_schemas import *
from services.resume_service import ResumeService
from services.file_storage_service import FileStorageService
from services.virus_scanner_service import VirusScannerService
from core.dependencies import get_current_user, require_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

# ============================================================================
# ENDPOINT 1: Single Resume Upload
# ============================================================================

@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    candidate_name: Optional[str] = Form(None),
    candidate_email: Optional[str] = Form(None),
    candidate_phone: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Upload a single resume
    
    - **file**: Resume file (max 10MB, formats: PDF, DOCX, TXT)
    - **candidate_name**: Optional candidate name
    - **candidate_email**: Optional candidate email
    - **candidate_phone**: Optional candidate phone
    
    Returns resume ID and upload details
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload resume
        result = await resume_service.upload_resume(
            file_content=file_content,
            file_name=file.filename,
            uploaded_by=current_user["id"],
            metadata={
                "candidate_name": candidate_name,
                "candidate_email": candidate_email,
                "candidate_phone": candidate_phone
            },
            ip_address=current_user.get("ip_address"),
            user_agent=current_user.get("user_agent")
        )
        
        # Schedule background tasks
        background_tasks.add_task(
            resume_service.process_resume,
            resume_id=result["resume_id"]
        )
        
        return ResumeUploadResponse(
            success=True,
            message="Resume uploaded successfully",
            data=result
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload resume"
        )

# ============================================================================
# ENDPOINT 2: Bulk Resume Upload
# ============================================================================

@router.post("/bulk-upload", status_code=status.HTTP_202_ACCEPTED)
async def bulk_upload_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Multiple resume files (max 50)"),
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Upload multiple resumes at once
    
    - **files**: List of resume files (max 50 files)
    
    Returns session ID for tracking progress
    """
    try:
        if len(files) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 files allowed per bulk upload"
            )
        
        # Create bulk upload session
        session = await resume_service.create_bulk_upload_session(
            user_id=current_user["id"],
            total_files=len(files)
        )
        
        # Process files in background
        background_tasks.add_task(
            resume_service.process_bulk_upload,
            session_id=session["session_id"],
            files=files,
            user_id=current_user["id"]
        )
        
        return {
            "success": True,
            "message": "Bulk upload initiated",
            "data": {
                "session_id": session["session_id"],
                "total_files": len(files),
                "status_url": f"/api/resumes/bulk-upload/{session['session_id']}/status"
            }
        }
    
    except Exception as e:
        logger.error(f"Bulk upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate bulk upload"
        )

# ============================================================================
# ENDPOINT 3: Bulk Upload Status
# ============================================================================

@router.get("/bulk-upload/{session_id}/status", response_model=BulkUploadStatusResponse)
async def get_bulk_upload_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Get status of bulk upload session
    
    - **session_id**: Bulk upload session ID
    
    Returns current progress and file statuses
    """
    try:
        status_data = await resume_service.get_bulk_upload_status(
            session_id=session_id,
            user_id=current_user["id"]
        )
        
        return BulkUploadStatusResponse(**status_data)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

# ============================================================================
# ENDPOINT 4: List Resumes (Paginated)
# ============================================================================

@router.get("", response_model=PaginatedResumeResponse)
async def list_resumes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ResumeStatus] = None,
    uploaded_by: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Get paginated list of resumes
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **status**: Filter by status
    - **uploaded_by**: Filter by uploader user ID
    - **search**: Search in candidate name, email, or filename
    
    Returns paginated list of resumes
    """
    try:
        result = await resume_service.list_resumes(
            page=page,
            limit=limit,
            status=status,
            uploaded_by=uploaded_by,
            search=search,
            current_user_id=current_user["id"],
            current_user_role=current_user["role"]
        )
        
        return PaginatedResumeResponse(
            success=True,
            data=result
        )
    
    except Exception as e:
        logger.error(f"List resumes error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resumes"
        )

# ============================================================================
# ENDPOINT 5: Get Resume Details
# ============================================================================

@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume_details(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Get detailed information about a resume
    
    - **resume_id**: Resume UUID
    
    Returns complete resume details
    """
    try:
        resume = await resume_service.get_resume_by_id(
            resume_id=resume_id,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        return ResumeDetailResponse(**resume)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get resume error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume details"
        )

# ============================================================================
# ENDPOINT 6: Download Resume
# ============================================================================

@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(),
    file_storage: FileStorageService = Depends()
):
    """
    Download resume file
    
    - **resume_id**: Resume UUID
    
    Returns file for download
    """
    try:
        resume = await resume_service.get_resume_by_id(
            resume_id=resume_id,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        file_path = await file_storage.get_file_path(resume["file_path"])
        
        return FileResponse(
            path=file_path,
            filename=resume["original_file_name"],
            media_type=resume["mime_type"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download resume"
        )

# ============================================================================
# ENDPOINT 7: Delete Resume
# ============================================================================

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Delete a resume (soft delete)
    
    - **resume_id**: Resume UUID
    
    Only admins or the uploader can delete
    """
    try:
        await resume_service.delete_resume(
            resume_id=resume_id,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        return {
            "success": True,
            "message": "Resume deleted successfully"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume"
        )

# ============================================================================
# ENDPOINT 8: Check Duplicate
# ============================================================================

@router.post("/check-duplicate", response_model=DuplicateDetectionResponse)
async def check_duplicate(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Check if resume is a duplicate
    
    - **file**: Resume file to check
    
    Returns duplicate status and existing resume info if duplicate
    """
    try:
        file_content = await file.read()
        result = await resume_service.check_duplicate(file_content)
        
        return DuplicateDetectionResponse(**result)
    
    except Exception as e:
        logger.error(f"Duplicate check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for duplicates"
        )

# ============================================================================
# ENDPOINT 9: Get Resume Preview
# ============================================================================

@router.get("/{resume_id}/preview")
async def get_resume_preview(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends()
):
    """
    Get resume preview (first page for PDF/DOCX)
    
    - **resume_id**: Resume UUID
    
    Returns preview image or text
    """
    try:
        preview = await resume_service.generate_preview(
            resume_id=resume_id,
            user_id=current_user["id"]
        )
        
        return preview
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview"
        )
```

---

## 3. SERVICE LAYER

### 3.1 File Storage Service

```python
# services/file_storage_service.py

import os
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class FileStorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        self.base_upload_dir = settings.upload_dir
        self.ensure_upload_directory()
    
    def ensure_upload_directory(self):
        """Create upload directory if it doesn't exist"""
        Path(self.base_upload_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_file_path(self, user_id: str, resume_id: str, file_extension: str) -> str:
        """
        Generate organized file path
        
        Structure: uploads/{year}/{month}/{user_id}/{resume_id}.{ext}
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        # Create directory structure
        dir_path = os.path.join(
            self.base_upload_dir,
            year,
            month,
            user_id
        )
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Generate file path
        file_name = f"{resume_id}.{file_extension}"
        return os.path.join(dir_path, file_name)
    
    async def save_file(self, file_content: bytes, file_path: str) -> bool:
        """
        Save file to storage
        
        Args:
            file_content: File binary content
            file_path: Destination file path
            
        Returns:
            True if successful
        """
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"File saved successfully: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise ValueError(f"Failed to save file: {str(e)}")
    
    async def read_file(self, file_path: str) -> bytes:
        """Read file from storage"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            return content
        
        except FileNotFoundError:
            raise ValueError("File not found")
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise ValueError(f"Failed to read file: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    async def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size: {str(e)}")
            return 0
    
    def get_file_path(self, relative_path: str) -> str:
        """Convert relative path to absolute path"""
        return os.path.join(self.base_upload_dir, relative_path)
```

### 3.2 File Validator Service

```python
# services/file_validator_service.py

import hashlib
import magic
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

class FileValidatorService:
    """Service for validating uploaded files"""
    
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    MIME_TYPES = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain'
    }
    
    def validate_file(self, file_content: bytes, file_name: str) -> Tuple[bool, List[str]]:
        """
        Validate file content and name
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate file size
        if len(file_content) == 0:
            errors.append("File is empty")
        elif len(file_content) > self.MAX_FILE_SIZE:
            errors.append(f"File size exceeds maximum limit of {self.MAX_FILE_SIZE / (1024*1024):.0f}MB")
        
        # Validate file extension
        file_ext = self.get_file_extension(file_name)
        if file_ext not in self.ALLOWED_EXTENSIONS:
            errors.append(f"Invalid file format. Allowed formats: {', '.join(self.ALLOWED_EXTENSIONS)}")
        
        # Validate MIME type (magic bytes)
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            expected_mime = self.MIME_TYPES.get(file_ext.lstrip('.'))
            
            if expected_mime and mime_type != expected_mime:
                errors.append(f"File content doesn't match extension. Detected: {mime_type}")
        except Exception as e:
            logger.warning(f"MIME type detection failed: {str(e)}")
        
        return (len(errors) == 0, errors)
    
    def get_file_extension(self, file_name: str) -> str:
        """Extract file extension"""
        return os.path.splitext(file_name)[1].lower()
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file"""
        return hashlib.sha256(file_content).hexdigest()
    
    def get_mime_type(self, file_content: bytes) -> str:
        """Detect MIME type from file content"""
        try:
            return magic.from_buffer(file_content, mime=True)
        except Exception as e:
            logger.error(f"MIME type detection error: {str(e)}")
            return "application/octet-stream"
```

### 3.3 Virus Scanner Service

```python
# services/virus_scanner_service.py

import clamd
from typing import Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VirusScannerService:
    """Service for scanning files for viruses using ClamAV"""
    
    def __init__(self):
        try:
            self.scanner = clamd.ClamdUnixSocket()
            self.scanner.ping()
            self.available = True
            logger.info("ClamAV scanner initialized successfully")
        except Exception as e:
            logger.warning(f"ClamAV not available: {str(e)}")
            self.available = False
    
    async def scan_file(self, file_content: bytes) -> Dict:
        """
        Scan file for viruses
        
        Returns:
            {
                "status": "clean|infected|failed",
                "scan_date": datetime,
                "result": "scan details",
                "is_safe": bool
            }
        """
        if not self.available:
            return {
                "status": "failed",
                "scan_date": datetime.utcnow(),
                "result": "Scanner not available",
                "is_safe": False  # Fail secure
            }
        
        try:
            # Scan file content
            scan_result = self.scanner.scan_stream(file_content)
            
            # Parse result
            if scan_result is None:
                # No threats found
                return {
                    "status": "clean",
                    "scan_date": datetime.utcnow(),
                    "result": "No threats detected",
                    "is_safe": True
                }
            else:
                # Threat detected
                threat_name = scan_result.get('stream', ['UNKNOWN'])[1]
                return {
                    "status": "infected",
                    "scan_date": datetime.utcnow(),
                    "result": f"Threat detected: {threat_name}",
                    "is_safe": False
                }
        
        except Exception as e:
            logger.error(f"Virus scan error: {str(e)}")
            return {
                "status": "failed",
                "scan_date": datetime.utcnow(),
                "result": f"Scan failed: {str(e)}",
                "is_safe": False  # Fail secure
            }
```

### 3.4 Resume Service (Main Business Logic)

```python
# services/resume_service.py

from typing import Dict, List, Optional
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
import logging

from models.database import Resume, ResumeUploadHistory, BulkUploadSession
from services.file_storage_service import FileStorageService
from services.file_validator_service import FileValidatorService
from services.virus_scanner_service import VirusScannerService

logger = logging.getLogger(__name__)

class ResumeService:
    """Main service for resume operations"""
    
    def __init__(
        self,
        db_session: AsyncSession,
        file_storage: FileStorageService,
        file_validator: FileValidatorService,
        virus_scanner: VirusScannerService
    ):
        self.db = db_session
        self.file_storage = file_storage
        self.file_validator = file_validator
        self.virus_scanner = virus_scanner
    
    async def upload_resume(
        self,
        file_content: bytes,
        file_name: str,
        uploaded_by: str,
        metadata: Dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict:
        """
        Upload a single resume
        
        Returns:
            {
                "resume_id": str,
                "file_name": str,
                "file_size": int,
                "file_type": str,
                "upload_date": datetime,
                "virus_scan_status": str,
                "is_duplicate": bool
            }
        """
        try:
            # 1. Validate file
            is_valid, errors = self.file_validator.validate_file(file_content, file_name)
            if not is_valid:
                raise ValueError("; ".join(errors))
            
            # 2. Calculate file hash
            file_hash = self.file_validator.calculate_file_hash(file_content)
            
            # 3. Check for duplicates
            duplicate = await self._check_duplicate(file_hash)
            if duplicate:
                return {
                    "is_duplicate": True,
                    "existing_resume": duplicate
                }
            
            # 4. Scan for viruses
            scan_result = await self.virus_scanner.scan_file(file_content)
            if not scan_result["is_safe"]:
                raise ValueError(f"Security threat detected: {scan_result['result']}")
            
            # 5. Generate file path and save
            resume_id = str(uuid.uuid4())
            file_ext = self.file_validator.get_file_extension(file_name).lstrip('.')
            file_path = self.file_storage.generate_file_path(uploaded_by, resume_id, file_ext)
            
            await self.file_storage.save_file(file_content, file_path)
            
            # 6. Create database record
            resume = Resume(
                id=resume_id,
                file_name=f"{resume_id}.{file_ext}",
                original_file_name=file_name,
                file_path=file_path,
                file_size=len(file_content),
                file_type=file_ext,
                file_hash=file_hash,
                mime_type=self.file_validator.get_mime_type(file_content),
                candidate_name=metadata.get("candidate_name"),
                candidate_email=metadata.get("candidate_email"),
                candidate_phone=metadata.get("candidate_phone"),
                uploaded_by=uploaded_by,
                upload_ip=ip_address,
                upload_user_agent=user_agent,
                status="uploaded",
                virus_scan_status=scan_result["status"],
                virus_scan_date=scan_result["scan_date"],
                virus_scan_result=scan_result["result"]
            )
            
            self.db.add(resume)
            
            # 7. Log upload history
            history = ResumeUploadHistory(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                action="uploaded",
                performed_by=uploaded_by,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"file_name": file_name, "file_size": len(file_content)}
            )
            
            self.db.add(history)
            await self.db.commit()
            
            logger.info(f"Resume uploaded successfully: {resume_id}")
            
            return {
                "resume_id": resume_id,
                "file_name": file_name,
                "file_size": len(file_content),
                "file_type": file_ext,
                "upload_date": resume.upload_date,
                "virus_scan_status": scan_result["status"],
                "is_duplicate": False
            }
        
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Upload error: {str(e)}")
            raise ValueError("Failed to upload resume")
    
    async def _check_duplicate(self, file_hash: str) -> Optional[Dict]:
        """Check if file hash exists in database"""
        result = await self.db.execute(
            select(Resume).where(
                and_(
                    Resume.file_hash == file_hash,
                    Resume.deleted_at.is_(None)
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return {
                "resume_id": existing.id,
                "file_name": existing.original_file_name,
                "uploaded_by": existing.uploaded_by,
                "upload_date": existing.upload_date
            }
        
        return None
    
    async def list_resumes(
        self,
        page: int,
        limit: int,
        status: Optional[str],
        uploaded_by: Optional[str],
        search: Optional[str],
        current_user_id: str,
        current_user_role: str
    ) -> Dict:
        """Get paginated list of resumes"""
        # Build query
        query = select(Resume).where(Resume.deleted_at.is_(None))
        
        # Apply filters
        if status:
            query = query.where(Resume.status == status)
        
        if uploaded_by:
            query = query.where(Resume.uploaded_by == uploaded_by)
        elif current_user_role == "recruiter":
            # Recruiters see only their own uploads
            query = query.where(Resume.uploaded_by == current_user_id)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Resume.candidate_name.ilike(search_pattern),
                    Resume.candidate_email.ilike(search_pattern),
                    Resume.original_file_name.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit).order_by(Resume.upload_date.desc())
        
        # Execute query
        result = await self.db.execute(query)
        resumes = result.scalars().all()
        
        return {
            "resumes": [self._format_resume_list_item(r) for r in resumes],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    
    def _format_resume_list_item(self, resume: Resume) -> Dict:
        """Format resume for list view"""
        return {
            "id": resume.id,
            "file_name": resume.original_file_name,
            "candidate_name": resume.candidate_name,
            "candidate_email": resume.candidate_email,
            "upload_date": resume.upload_date,
            "uploaded_by_name": "User",  # TODO: Join with users table
            "status": resume.status,
            "file_size": resume.file_size,
            "virus_scan_status": resume.virus_scan_status
        }
```

---

## 4. UI/UX DESIGN

### 4.1 Upload Page Template

```html
<!-- templates/resumes/upload.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Resumes - HR Recruitment System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .upload-zone {
            border: 3px dashed #ccc;
            border-radius: 10px;
            padding: 60px 20px;
            text-align: center;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-zone.dragover {
            border-color: #0d6efd;
            background: #e7f1ff;
        }
        .file-item {
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            background: white;
        }
        .file-item.error {
            border-color: #dc3545;
            background: #f8d7da;
        }
        .file-item.success {
            border-color: #198754;
            background: #d1e7dd;
        }
        .progress-container {
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <h2 class="mb-4">
                    <i class="fas fa-file-upload text-primary"></i> Upload Resumes
                </h2>

                <!-- Upload Zone -->
                <div class="upload-zone" id="uploadZone">
                    <i class="fas fa-cloud-upload-alt fa-4x text-muted mb-3"></i>
                    <h4>Drag & Drop Files Here</h4>
                    <p class="text-muted">or click to browse</p>
                    <p class="small text-muted">
                        Supported: PDF, DOCX, TXT | Max size: 10MB | Bulk limit: 50 files
                    </p>
                    <input type="file" id="fileInput" multiple accept=".pdf,.docx,.txt" style="display: none;">
                    <button class="btn btn-primary mt-3" onclick="document.getElementById('fileInput').click()">
                        <i class="fas fa-folder-open"></i> Browse Files
                    </button>
                </div>

                <!-- Selected Files List -->
                <div id="filesList" class="mt-4" style="display: none;">
                    <h5>Selected Files (<span id="fileCount">0</span>)</h5>
                    <div id="filesContainer"></div>
                    
                    <div class="mt-3">
                        <button class="btn btn-success btn-lg" id="uploadBtn">
                            <i class="fas fa-upload"></i> Upload All (<span id="uploadCount">0</span> files)
                        </button>
                        <button class="btn btn-secondary btn-lg" id="clearBtn">
                            <i class="fas fa-times"></i> Clear All
                        </button>
                    </div>
                </div>

                <!-- Upload Progress Modal -->
                <div class="modal fade" id="progressModal" data-bs-backdrop="static" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-spinner fa-spin"></i> Uploading Resumes...
                                </h5>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Overall Progress</span>
                                        <span id="overallProgress">0%</span>
                                    </div>
                                    <div class="progress">
                                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                             id="overallProgressBar" style="width: 0%"></div>
                                    </div>
                                </div>
                                
                                <div id="uploadStatusList"></div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" id="cancelUploadBtn">
                                    Cancel Upload
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let selectedFiles = [];
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const filesList = document.getElementById('filesList');
        const filesContainer = document.getElementById('filesContainer');
        const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));

        // Drag and drop handlers
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });

        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        function handleFiles(files) {
            if (files.length > 50) {
                alert('Maximum 50 files allowed per upload');
                return;
            }

            selectedFiles = Array.from(files);
            displayFiles();
        }

        function displayFiles() {
            filesContainer.innerHTML = '';
            
            selectedFiles.forEach((file, index) => {
                const fileItem = createFileItem(file, index);
                filesContainer.appendChild(fileItem);
            });

            filesList.style.display = 'block';
            document.getElementById('fileCount').textContent = selectedFiles.length;
            document.getElementById('uploadCount').textContent = selectedFiles.length;
        }

        function createFileItem(file, index) {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.id = `file-${index}`;

            const isValid = validateFile(file);
            if (!isValid.valid) {
                div.classList.add('error');
            }

            div.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1">
                        <i class="fas fa-file-${getFileIcon(file.name)} me-2"></i>
                        <strong>${file.name}</strong>
                        <span class="text-muted ms-2">(${formatFileSize(file.size)})</span>
                        ${!isValid.valid ? `<br><small class="text-danger">${isValid.error}</small>` : ''}
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="removeFile(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="progress-container" id="progress-${index}" style="display: none;">
                    <div class="progress mt-2">
                        <div class="progress-bar" style="width: 0%"></div>
                    </div>
                </div>
            `;

            return div;
        }

        function validateFile(file) {
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['.pdf', '.docx', '.txt'];
            const ext = '.' + file.name.split('.').pop().toLowerCase();

            if (file.size > maxSize) {
                return { valid: false, error: 'File size exceeds 10MB limit' };
            }

            if (!allowedTypes.includes(ext)) {
                return { valid: false, error: 'Invalid file format. Allowed: PDF, DOCX, TXT' };
            }

            return { valid: true };
        }

        function getFileIcon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const icons = {
                'pdf': 'pdf',
                'docx': 'word',
                'txt': 'alt'
            };
            return icons[ext] || 'file';
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function removeFile(index) {
            selectedFiles.splice(index, 1);
            displayFiles();
            
            if (selectedFiles.length === 0) {
                filesList.style.display = 'none';
            }
        }

        document.getElementById('clearBtn').addEventListener('click', () => {
            selectedFiles = [];
            filesList.style.display = 'none';
            fileInput.value = '';
        });

        document.getElementById('uploadBtn').addEventListener('click', async () => {
            const validFiles = selectedFiles.filter(f => validateFile(f).valid);
            
            if (validFiles.length === 0) {
                alert('No valid files to upload');
                return;
            }

            progressModal.show();
            await uploadFiles(validFiles);
        });

        async function uploadFiles(files) {
            const token = localStorage.getItem('access_token');
            let successful = 0;
            let failed = 0;

            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/api/resumes/upload', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        },
                        body: formData
                    });

                    if (response.ok) {
                        successful++;
                        updateFileStatus(i, 'success');
                    } else {
                        failed++;
                        const error = await response.json();
                        updateFileStatus(i, 'error', error.detail);
                    }
                } catch (error) {
                    failed++;
                    updateFileStatus(i, 'error', error.message);
                }

                updateOverallProgress((i + 1) / files.length * 100);
            }

            // Show summary
            setTimeout(() => {
                progressModal.hide();
                alert(`Upload complete!\nSuccessful: ${successful}\nFailed: ${failed}`);
                
                if (successful > 0) {
                    window.location.href = '/resumes';
                }
            }, 1000);
        }

        function updateFileStatus(index, status, message = '') {
            const fileItem = document.getElementById(`file-${index}`);
            if (status === 'success') {
                fileItem.classList.add('success');
                fileItem.innerHTML += '<i class="fas fa-check-circle text-success float-end"></i>';
            } else if (status === 'error') {
                fileItem.classList.add('error');
                fileItem.innerHTML += `<br><small class="text-danger">${message}</small>`;
            }
        }

        function updateOverallProgress(percentage) {
            const progressBar = document.getElementById('overallProgressBar');
            const progressText = document.getElementById('overallProgress');
            
            progressBar.style.width = percentage + '%';
            progressText.textContent = Math.round(percentage) + '%';
        }
    </script>
</body>
</html>
```

### 4.2 Resume List Page

```html
<!-- templates/resumes/list.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resumes - HR Recruitment System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2><i class="fas fa-file-alt text-primary"></i> Resumes</h2>
                    <a href="/resumes/upload" class="btn btn-primary">
                        <i class="fas fa-upload"></i> Upload Resume
                    </a>
                </div>

                <!-- Filters -->
                <div class="card mb-4">
                    <div class="card-body">
                        <div class="row g-3">
                            <div class="col-md-3">
                                <input type="text" class="form-control" id="searchInput" placeholder="Search...">
                            </div>
                            <div class="col-md-2">
                                <select class="form-select" id="statusFilter">
                                    <option value="">All Status</option>
                                    <option value="uploaded">Uploaded</option>
                                    <option value="parsing">Parsing</option>
                                    <option value="parsed">Parsed</option>
                                    <option value="failed">Failed</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <button class="btn btn-secondary w-100" id="filterBtn">
                                    <i class="fas fa-filter"></i> Apply Filters
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Resumes Table -->
                <div class="card">
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Candidate</th>
                                        <th>Email</th>
                                        <th>Upload Date</th>
                                        <th>Uploaded By</th>
                                        <th>Status</th>
                                        <th>Size</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="resumesTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>

                        <!-- Pagination -->
                        <nav id="paginationNav" class="mt-3">
                            <ul class="pagination justify-content-center" id="pagination">
                                <!-- Populated by JavaScript -->
                            </ul>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentPage = 1;
        const limit = 20;

        async function loadResumes(page = 1) {
            const token = localStorage.getItem('access_token');
            const search = document.getElementById('searchInput').value;
            const status = document.getElementById('statusFilter').value;

            const params = new URLSearchParams({
                page: page,
                limit: limit,
                ...(search && { search }),
                ...(status && { status })
            });

            try {
                const response = await fetch(`/api/resumes?${params}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                const data = await response.json();
                
                if (data.success) {
                    displayResumes(data.data.resumes);
                    displayPagination(data.data.pagination);
                }
            } catch (error) {
                console.error('Error loading resumes:', error);
            }
        }

        function displayResumes(resumes) {
            const tbody = document.getElementById('resumesTableBody');
            tbody.innerHTML = '';

            resumes.forEach(resume => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <i class="fas fa-file-${getFileIcon(resume.file_name)} me-2"></i>
                        ${resume.file_name}
                    </td>
                    <td>${resume.candidate_name || '-'}</td>
                    <td>${resume.candidate_email || '-'}</td>
                    <td>${new Date(resume.upload_date).toLocaleString()}</td>
                    <td>${resume.uploaded_by_name}</td>
                    <td>
                        <span class="badge bg-${getStatusColor(resume.status)}">
                            ${resume.status}
                        </span>
                    </td>
                    <td>${formatFileSize(resume.file_size)}</td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="viewResume('${resume.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-success" onclick="downloadResume('${resume.id}')">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteResume('${resume.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function displayPagination(pagination) {
            const paginationEl = document.getElementById('pagination');
            paginationEl.innerHTML = '';

            for (let i = 1; i <= pagination.total_pages; i++) {
                const li = document.createElement('li');
                li.className = `page-item ${i === pagination.page ? 'active' : ''}`;
                li.innerHTML = `<a class="page-link" href="#" onclick="loadResumes(${i}); return false;">${i}</a>`;
                paginationEl.appendChild(li);
            }
        }

        function getFileIcon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const icons = { 'pdf': 'pdf', 'docx': 'word', 'txt': 'alt' };
            return icons[ext] || 'file';
        }

        function getStatusColor(status) {
            const colors = {
                'uploaded': 'primary',
                'parsing': 'warning',
                'parsed': 'success',
                'failed': 'danger'
            };
            return colors[status] || 'secondary';
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        async function downloadResume(id) {
            const token = localStorage.getItem('access_token');
            window.location.href = `/api/resumes/${id}/download?token=${token}`;
        }

        async function deleteResume(id) {
            if (!confirm('Are you sure you want to delete this resume?')) return;

            const token = localStorage.getItem('access_token');
            try {
                const response = await fetch(`/api/resumes/${id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    alert('Resume deleted successfully');
                    loadResumes(currentPage);
                }
            } catch (error) {
                console.error('Delete error:', error);
                alert('Failed to delete resume');
            }
        }

        document.getElementById('filterBtn').addEventListener('click', () => {
            loadResumes(1);
        });

        // Load resumes on page load
        loadResumes();
    </script>
</body>
</html>
```

---

## 5. INTEGRATION POINTS

### 5.1 Authentication Integration

```python
# Integration with existing auth system

from core.dependencies import get_current_user

# All resume endpoints require authentication
@router.post("/upload")
async def upload_resume(
    current_user: dict = Depends(get_current_user),  # ← Uses existing auth
    ...
):
    # current_user contains: {id, email, full_name, role}
    uploaded_by = current_user["id"]
    ...
```

### 5.2 Database Integration

```python
# Update core/database.py to include new models

from models.database import Resume, ResumeUploadHistory, BulkUploadSession, ResumeVersion

# Models will be auto-discovered by SQLAlchemy
```

### 5.3 File Storage Integration

```python
# Update core/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Resume Upload Settings
    resume_upload_dir: str = "uploads/resumes"
    max_resume_size: int = 10 * 1024 * 1024  # 10MB
    allowed_resume_formats: list = [".pdf", ".docx", ".txt"]
    enable_virus_scanning: bool = True
    clamav_socket: str = "/var/run/clamav/clamd.ctl"
```

### 5.4 Celery Task Integration

```python
# tasks/resume_tasks.py

from celery import shared_task
from services.resume_service import ResumeService

@shared_task
def process_resume_async(resume_id: str):
    """
    Background task to process resume:
    1. Extract text
    2. Parse data (skills, experience, etc.)
    3. Update resume status
    """
    # Implementation here
    pass

@shared_task
def cleanup_failed_uploads():
    """
    Scheduled task to clean up failed uploads older than 24 hours
    """
    # Implementation here
    pass
```

---

## 6. FILE STRUCTURE

### 6.1 New Files to Create

```
kp-ai-hr-recruitement-assistant/
├── api/
│   └── resumes.py                          # NEW: Resume API endpoints
├── models/
│   ├── resume_schemas.py                   # NEW: Pydantic models for resumes
│   └── database.py                         # MODIFY: Add Resume models
├── services/
│   ├── resume_service.py                   # NEW: Main resume business logic
│   ├── file_storage_service.py             # NEW: File storage operations
│   ├── file_validator_service.py           # NEW: File validation
│   └── virus_scanner_service.py            # NEW: Virus scanning
├── templates/
│   └── resumes/
│       ├── upload.html                     # NEW: Upload page
│       ├── list.html                       # NEW: Resume list page
│       └── detail.html                     # NEW: Resume detail page
├── migrations/
│   └── versions/
│       └── 002_create_resume_tables.py     # NEW: Database migration
├── tests/
│   ├── test_resume_service.py              # NEW: Resume service tests
│   ├── test_file_validator.py              # NEW: File validator tests
│   └── test_resume_api.py                  # NEW: API integration tests
├── tasks/
│   └── resume_tasks.py                     # NEW: Celery tasks
└── uploads/
    └── resumes/                            # NEW: Resume storage directory
```

### 6.2 Files to Modify

```python
# main.py - Add resume router
from api import resumes

app.include_router(resumes.router)

# Add route for upload page
@app.get("/resumes/upload", response_class=HTMLResponse)
async def resume_upload_page(request: Request):
    return templates.TemplateResponse("resumes/upload.html", {"request": request})

@app.get("/resumes", response_class=HTMLResponse)
async def resumes_list_page(request: Request):
    return templates.TemplateResponse("resumes/list.html", {"request": request})
```

```python
# core/config.py - Add resume settings
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Resume Upload Settings
    resume_upload_dir: str = "uploads/resumes"
    max_resume_size: int = 10 * 1024 * 1024
    allowed_resume_formats: list = [".pdf", ".docx", ".txt"]
    enable_virus_scanning: bool = True
    clamav_socket: str = "/var/run/clamav/clamd.ctl"
    resume_retention_years: int = 2
    failed_upload_cleanup_hours: int = 24
```

```python
# requirements.txt - Add new dependencies
python-magic>=0.4.27
clamd>=1.0.2
PyPDF2>=3.0.0
python-docx>=1.1.0
Pillow>=10.1.0
```

---

## 7. TESTING STRATEGY

### 7.1 Unit Tests

```python
# tests/test_file_validator.py

import pytest
from services.file_validator_service import FileValidatorService

@pytest.fixture
def validator():
    return FileValidatorService()

def test_validate_pdf_file(validator):
    """Test PDF file validation"""
    with open("test_files/sample.pdf", "rb") as f:
        content = f.read()
    
    is_valid, errors = validator.validate_file(content, "sample.pdf")
    assert is_valid == True
    assert len(errors) == 0

def test_validate_oversized_file(validator):
    """Test file size validation"""
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    
    is_valid, errors = validator.validate_file(large_content, "large.pdf")
    assert is_valid == False
    assert any("exceeds maximum limit" in error for error in errors)

def test_validate_invalid_format(validator):
    """Test invalid file format rejection"""
    is_valid, errors = validator.validate_file(b"content", "file.exe")
    assert is_valid == False
    assert any("Invalid file format" in error for error in errors)

def test_calculate_file_hash(validator):
    """Test SHA-256 hash calculation"""
    content = b"test content"
    hash1 = validator.calculate_file_hash(content)
    hash2 = validator.calculate_file_hash(content)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 produces 64 hex characters
```

```python
# tests/test_virus_scanner.py

import pytest
from services.virus_scanner_service import VirusScannerService

@pytest.fixture
def scanner():
    return VirusScannerService()

@pytest.mark.asyncio
async def test_scan_clean_file(scanner):
    """Test scanning clean file"""
    clean_content = b"This is a clean file"
    result = await scanner.scan_file(clean_content)
    
    assert result["status"] == "clean"
    assert result["is_safe"] == True

@pytest.mark.asyncio
async def test_scan_eicar_test_file(scanner):
    """Test scanning EICAR test virus file"""
    # EICAR test string
    eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    
    result = await scanner.scan_file(eicar)
    
    assert result["status"] == "infected"
    assert result["is_safe"] == False
    assert "EICAR" in result["result"]
```

### 7.2 Integration Tests

```python
# tests/test_resume_api.py

import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_upload_resume_success():
    """Test successful resume upload"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login first
        login_response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["data"]["tokens"]["access_token"]
        
        # Upload resume
        with open("test_files/sample_resume.pdf", "rb") as f:
            response = await client.post(
                "/api/resumes/upload",
                files={"file": ("resume.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] == True
        assert "resume_id" in data["data"]

@pytest.mark.asyncio
async def test_upload_invalid_file():
    """Test uploading invalid file format"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        token = await get_auth_token(client)
        
        response = await client.post(
            "/api/resumes/upload",
            files={"file": ("file.exe", b"content", "application/x-msdownload")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_resumes_pagination():
    """Test resume listing with pagination"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        token = await get_auth_token(client)
        
        response = await client.get(
            "/api/resumes?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "resumes" in data["data"]
        assert "pagination" in data["data"]
        assert data["data"]["pagination"]["page"] == 1
```

### 7.3 Manual Testing Checklist

#### Single Upload Flow
- [ ] Navigate to `/resumes/upload`
- [ ] Drag and drop a PDF file
- [ ] Verify file appears in selected files list
- [ ] Click "Upload All"
- [ ] Verify success message
- [ ] Check resume appears in list at `/resumes`

#### Bulk Upload Flow
- [ ] Select 10 PDF files
- [ ] Click "Upload All"
- [ ] Verify progress modal shows
- [ ] Verify all files upload successfully
- [ ] Check all 10 resumes in list

#### Duplicate Detection
- [ ] Upload a resume
- [ ] Upload the same file again
- [ ] Verify duplicate warning
- [ ] Test "Skip" option
- [ ] Test "Upload as new version" option

#### Virus Scanning
- [ ] Upload EICAR test file
- [ ] Verify file is rejected
- [ ] Verify error message mentions security threat

#### File Validation
- [ ] Try uploading .exe file → Should reject
- [ ] Try uploading 15MB file → Should reject
- [ ] Try uploading 0-byte file → Should reject

#### Permissions
- [ ] Login as recruiter
- [ ] Verify can only see own uploads
- [ ] Login as admin
- [ ] Verify can see all uploads
- [ ] Test delete permissions

---

## 8. DEPLOYMENT CONSIDERATIONS

### 8.1 Environment Variables

```bash
# .env

# Resume Upload Settings
RESUME_UPLOAD_DIR=uploads/resumes
MAX_RESUME_SIZE=10485760
ALLOWED_RESUME_FORMATS=.pdf,.docx,.txt
ENABLE_VIRUS_SCANNING=true
CLAMAV_SOCKET=/var/run/clamav/clamd.ctl

# Storage Settings (for cloud deployment)
USE_CLOUD_STORAGE=false
AWS_S3_BUCKET=hr-resumes
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# Celery Settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 8.2 Database Migration

```bash
# Run migration
alembic upgrade head

# Or using custom script
python scripts/migrate_database.py
```

### 8.3 ClamAV Setup

```bash
# Install ClamAV
sudo apt-get update
sudo apt-get install clamav clamav-daemon

# Update virus definitions
sudo freshclam

# Start ClamAV daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon

# Verify it's running
sudo systemctl status clamav-daemon
```

### 8.4 Storage Setup

```bash
# Create upload directory
mkdir -p uploads/resumes
chmod 755 uploads/resumes

# For production, ensure proper permissions
chown -R www-data:www-data uploads/
```

### 8.5 Celery Worker Setup

```bash
# Start Celery worker
celery -A tasks.resume_tasks worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A tasks.resume_tasks beat --loglevel=info

# For production, use supervisor or systemd
```

### 8.6 Nginx Configuration (if applicable)

```nginx
# Increase upload size limit
client_max_body_size 10M;

# Timeout for large uploads
client_body_timeout 300s;
```

### 8.7 Deployment Checklist

- [ ] Run database migrations
- [ ] Install and configure ClamAV
- [ ] Update virus definitions
- [ ] Create upload directories with proper permissions
- [ ] Configure environment variables
- [ ] Start Celery workers
- [ ] Test file upload functionality
- [ ] Verify virus scanning works
- [ ] Test bulk upload with 50 files
- [ ] Monitor disk space usage
- [ ] Set up automated cleanup jobs
- [ ] Configure backup for uploaded files
- [ ] Test disaster recovery procedures

---

## 9. PERFORMANCE CONSIDERATIONS

### 9.1 Optimization Strategies

1. **Chunked Uploads** for large files
2. **Async Processing** with Celery for virus scanning and parsing
3. **Database Indexing** on frequently queried columns
4. **Caching** for duplicate checks
5. **CDN** for serving downloaded resumes
6. **Compression** for stored files

### 9.2 Monitoring

```python
# Add metrics collection
from prometheus_client import Counter, Histogram

upload_counter = Counter('resume_uploads_total', 'Total resume uploads')
upload_duration = Histogram('resume_upload_duration_seconds', 'Upload duration')

@upload_duration.time()
async def upload_resume(...):
    upload_counter.inc()
    # ... upload logic
```

---

## 10. SECURITY CONSIDERATIONS

1. **File Validation**: Check both extension and MIME type
2. **Virus Scanning**: Mandatory before storage
3. **Access Control**: Role-based permissions
4. **Secure Storage**: Encrypted at rest
5. **Audit Logging**: Track all upload/download/delete operations
6. **Rate Limiting**: Prevent abuse
7. **Input Sanitization**: Clean filenames
8. **HTTPS Only**: For file transfers

---

**Implementation Status**: Ready for Development  
**Estimated Effort**: 6 weeks (120 hours)  
**Next Steps**: Begin Phase 1 implementation

---

*This technical implementation document provides all necessary details for developers to implement Feature 2: Resume Upload.*
