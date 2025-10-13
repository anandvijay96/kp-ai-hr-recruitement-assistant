"""Resume management API endpoints"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse
from typing import List, Optional
import logging

from models.resume_schemas import (
    ResumeUploadResponse,
    ResumeDetailResponse,
    PaginatedResumeResponse,
    BulkUploadStatusResponse,
    DuplicateDetectionResponse
)
from models.candidate_schemas import ParsedResumeData, DuplicateCheckResponse
from services.resume_service import ResumeService
from services.file_storage_service import FileStorageService
from services.file_validator_service import FileValidatorService
from services.resume_parser_service import ResumeParserService
from services.duplicate_detection_service import DuplicateDetectionService
from services.candidate_service import CandidateService
from core.dependencies import get_current_user
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


def get_resume_service(db: AsyncSession = Depends(get_db)) -> ResumeService:
    """Get resume service instance"""
    return ResumeService(
        db_session=db,
        file_storage=FileStorageService(),
        file_validator=FileValidatorService()
    )


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
    auto_parse: bool = Form(True, description="Automatically parse and create candidate"),
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a single resume and automatically create candidate
    
    - **file**: Resume file (max 10MB, formats: PDF, DOCX, TXT)
    - **candidate_name**: Optional candidate name
    - **candidate_email**: Optional candidate email
    - **candidate_phone**: Optional candidate phone
    - **auto_parse**: Automatically parse resume and create candidate (default: True)
    
    Returns resume ID, candidate ID (if created), and upload details
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
        
        # Check if duplicate
        if result.get("is_duplicate"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Duplicate resume detected",
                    "existing_resume": result["existing_resume"]
                }
            )
        
        resume_id = result.get("resume_id")
        candidate_id = None
        
        # Auto-parse and create candidate if requested
        if auto_parse and resume_id:
            try:
                # Parse resume
                parser = ResumeParserService()
                file_type = file.filename.split('.')[-1].lower()
                parsed_dict = await parser.parse_resume_structured(file_content, file_type)
                parsed_data = ParsedResumeData(**parsed_dict)
                
                # Check for duplicates
                duplicate_service = DuplicateDetectionService(db)
                duplicates = await duplicate_service.check_duplicates(
                    parsed_data=parsed_data,
                    resume_id=resume_id
                )
                
                # If no duplicates, create candidate automatically
                if not duplicates:
                    candidate_service = CandidateService(db)
                    candidate_id = await candidate_service.create_candidate_from_parsed_data(
                        parsed_data=parsed_data,
                        created_by=current_user["id"],
                        resume_id=resume_id
                    )
                    
                    # Update resume with candidate link
                    from models.database import Resume
                    from sqlalchemy import select
                    resume_result = await db.execute(
                        select(Resume).where(Resume.id == resume_id)
                    )
                    resume = resume_result.scalar_one_or_none()
                    if resume:
                        resume.candidate_id = candidate_id
                        resume.processing_status = "completed"
                        from datetime import datetime
                        resume.processed_at = datetime.utcnow()
                        await db.commit()
                    
                    result["candidate_id"] = candidate_id
                    result["candidate_created"] = True
                    logger.info(f"Auto-created candidate {candidate_id} for resume {resume_id}")
                else:
                    # Duplicates found - return them for user to resolve
                    result["duplicates_found"] = True
                    result["duplicates"] = duplicates
                    result["message"] = "Resume uploaded. Duplicate candidates found - please resolve."
                    logger.info(f"Duplicates found for resume {resume_id}: {len(duplicates)} matches")
                    
            except Exception as parse_error:
                logger.warning(f"Auto-parse failed for resume {resume_id}: {str(parse_error)}")
                result["parse_error"] = str(parse_error)
                result["message"] = "Resume uploaded but auto-parsing failed. You can manually parse later."
        
        return ResumeUploadResponse(
            success=True,
            message=result.get("message", "Resume uploaded successfully"),
            data=result
        )
    
    except HTTPException:
        raise
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
# ENDPOINT 2: List Resumes (Paginated)
# ============================================================================

@router.get("", response_model=PaginatedResumeResponse)
async def list_resumes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service)
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
# ENDPOINT 3: Get Resume Details
# ============================================================================

@router.get("/{resume_id}")
async def get_resume_details(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service)
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
        
        return {
            "success": True,
            "data": resume
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get resume error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume details"
        )


# ============================================================================
# ENDPOINT 4: Download Resume
# ============================================================================

@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service)
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
        
        file_storage = FileStorageService()
        file_path = file_storage.get_absolute_path(resume["file_path"])
        
        if not file_storage.file_exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file not found on server"
            )
        
        return FileResponse(
            path=file_path,
            filename=resume["original_file_name"],
            media_type="application/octet-stream"
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
# ENDPOINT 5: Delete Resume
# ============================================================================

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service)
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
# ENDPOINT 6: Check Duplicate
# ============================================================================

@router.post("/check-duplicate", response_model=DuplicateDetectionResponse)
async def check_duplicate(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service)
):
    """
    Check if resume is a duplicate
    
    - **file**: Resume file to check
    
    Returns duplicate status and existing resume info if duplicate
    """
    try:
        file_content = await file.read()
        file_validator = FileValidatorService()
        file_hash = file_validator.calculate_file_hash(file_content)
        
        duplicate = await resume_service._check_duplicate(file_hash)
        
        return DuplicateDetectionResponse(
            is_duplicate=bool(duplicate),
            existing_resume=duplicate,
            options=["skip", "replace", "new_version"]
        )
    
    except Exception as e:
        logger.error(f"Duplicate check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for duplicates"
        )


# ============================================================================
# ENDPOINT 7: Bulk Upload Session
# ============================================================================

@router.post("/bulk-upload", status_code=status.HTTP_202_ACCEPTED)
async def create_bulk_upload_session(
    total_files: int = Form(..., ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service)
):
    """
    Create a bulk upload session
    
    - **total_files**: Total number of files to upload (max 50)
    
    Returns session ID for tracking
    """
    try:
        session = await resume_service.create_bulk_upload_session(
            user_id=current_user["id"],
            total_files=total_files
        )
        
        return {
            "success": True,
            "message": "Bulk upload session created",
            "data": {
                "session_id": session["session_id"],
                "total_files": total_files,
                "status_url": f"/api/resumes/bulk-upload/{session['session_id']}/status"
            }
        }
    
    except Exception as e:
        logger.error(f"Bulk upload session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk upload session"
        )


# ============================================================================
# ENDPOINT 8: Bulk Upload Status
# ============================================================================

@router.get("/bulk-upload/{session_id}/status", response_model=BulkUploadStatusResponse)
async def get_bulk_upload_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service)
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
    except Exception as e:
        logger.error(f"Bulk upload status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bulk upload status"
        )


# ============================================================================
# ENDPOINT 9: Parse Resume and Create Candidate
# ============================================================================

@router.post("/{resume_id}/parse")
async def parse_resume_and_create_candidate(
    resume_id: str,
    check_duplicates: bool = Query(True, description="Check for duplicate candidates"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Parse resume and create candidate record
    
    - **resume_id**: Resume UUID
    - **check_duplicates**: Whether to check for duplicates before creating
    
    Returns parsed data and candidate ID if created
    """
    try:
        from models.database import Resume
        from sqlalchemy import select
        
        # Get resume
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Read file content
        file_storage = FileStorageService()
        file_path = file_storage.get_absolute_path(resume.file_path)
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Parse resume
        parser = ResumeParserService()
        parsed_dict = await parser.parse_resume_structured(file_content, resume.file_type)
        parsed_data = ParsedResumeData(**parsed_dict)
        
        # Check for duplicates if requested
        duplicates = []
        if check_duplicates:
            duplicate_service = DuplicateDetectionService(db)
            duplicates = await duplicate_service.check_duplicates(
                parsed_data=parsed_data,
                resume_id=resume_id
            )
        
        # If duplicates found, return them for user decision
        if duplicates:
            return {
                "success": True,
                "status": "duplicates_found",
                "parsed_data": parsed_dict,
                "duplicates": duplicates,
                "message": "Duplicate candidates found. Please resolve before creating."
            }
        
        # Create candidate
        candidate_service = CandidateService(db)
        candidate_id = await candidate_service.create_candidate_from_parsed_data(
            parsed_data=parsed_data,
            created_by=current_user["id"],
            resume_id=resume_id
        )
        
        # Update resume status
        resume.processing_status = "completed"
        resume.candidate_id = candidate_id
        from datetime import datetime
        resume.processed_at = datetime.utcnow()
        await db.commit()
        
        return {
            "success": True,
            "status": "candidate_created",
            "message": "Resume parsed and candidate created successfully",
            "data": {
                "candidate_id": candidate_id,
                "parsed_data": parsed_dict
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing resume {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume: {str(e)}"
        )


# ============================================================================
# ENDPOINT 10: Check for Duplicate Candidates
# ============================================================================

@router.post("/check-duplicate-candidate", response_model=DuplicateCheckResponse)
async def check_duplicate_candidate(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if uploaded resume matches existing candidates
    
    - **file**: Resume file to check
    
    Returns list of potential duplicate candidates
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'txt']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type"
            )
        
        # Parse resume
        parser = ResumeParserService()
        parsed_dict = await parser.parse_resume_structured(file_content, file_extension)
        parsed_data = ParsedResumeData(**parsed_dict)
        
        # Check for duplicates
        duplicate_service = DuplicateDetectionService(db)
        duplicates = await duplicate_service.check_duplicates(parsed_data=parsed_data)
        
        return DuplicateCheckResponse(
            is_duplicate=len(duplicates) > 0,
            duplicates=duplicates,
            options=["skip", "merge", "force_create"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking duplicate candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for duplicates"
        )


# ============================================================================
# ENDPOINT 11: Resolve Duplicate
# ============================================================================

@router.post("/{resume_id}/resolve-duplicate")
async def resolve_duplicate(
    resume_id: str,
    action: str = Form(..., description="Action: skip, merge, or force_create"),
    matched_candidate_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve a duplicate candidate situation
    
    - **resume_id**: Resume UUID
    - **action**: Resolution action (skip, merge, force_create)
    - **matched_candidate_id**: ID of matched candidate (required for merge)
    
    Returns result of the resolution
    """
    try:
        from models.database import Resume
        from sqlalchemy import select
        
        # Validate action
        if action not in ["skip", "merge", "force_create"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be: skip, merge, or force_create"
            )
        
        # Get resume
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        duplicate_service = DuplicateDetectionService(db)
        
        if action == "skip":
            # Mark as resolved, don't create candidate
            await duplicate_service.resolve_duplicate(
                resume_id=resume_id,
                resolution="skip",
                resolved_by=current_user["id"],
                matched_candidate_id=matched_candidate_id
            )
            
            return {
                "success": True,
                "message": "Duplicate skipped. No candidate created."
            }
        
        elif action == "merge":
            # Merge with existing candidate
            if not matched_candidate_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="matched_candidate_id required for merge action"
                )
            
            # Link resume to existing candidate
            resume.candidate_id = matched_candidate_id
            await db.commit()
            
            await duplicate_service.resolve_duplicate(
                resume_id=resume_id,
                resolution="merge",
                resolved_by=current_user["id"],
                matched_candidate_id=matched_candidate_id
            )
            
            return {
                "success": True,
                "message": "Resume merged with existing candidate",
                "data": {
                    "candidate_id": matched_candidate_id
                }
            }
        
        elif action == "force_create":
            # Create new candidate despite duplicates
            file_storage = FileStorageService()
            file_path = file_storage.get_absolute_path(resume.file_path)
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            parser = ResumeParserService()
            parsed_dict = await parser.parse_resume_structured(file_content, resume.file_type)
            parsed_data = ParsedResumeData(**parsed_dict)
            
            candidate_service = CandidateService(db)
            candidate_id = await candidate_service.create_candidate_from_parsed_data(
                parsed_data=parsed_data,
                created_by=current_user["id"],
                resume_id=resume_id
            )
            
            resume.candidate_id = candidate_id
            await db.commit()
            
            await duplicate_service.resolve_duplicate(
                resume_id=resume_id,
                resolution="force_create",
                resolved_by=current_user["id"],
                matched_candidate_id=matched_candidate_id
            )
            
            return {
                "success": True,
                "message": "New candidate created",
                "data": {
                    "candidate_id": candidate_id
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving duplicate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve duplicate"
        )
