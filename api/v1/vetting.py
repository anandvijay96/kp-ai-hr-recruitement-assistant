"""
Resume Vetting API
Endpoints for scanning resumes without saving to database
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import hashlib
import uuid
import os
import aiofiles

from core.database import get_db
from services.document_processor import DocumentProcessor
from services.resume_analyzer import ResumeAuthenticityAnalyzer
from services.jd_matcher import JDMatcher
from services.vetting_session import VettingSession
from services.google_search_verifier import GoogleSearchVerifier
from services.resume_data_extractor import ResumeDataExtractor
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Google Search Verifier (if configured)
google_search_verifier = None
if settings.google_search_api_key and settings.google_search_engine_id:
    try:
        google_search_verifier = GoogleSearchVerifier(
            api_key=settings.google_search_api_key,
            search_engine_id=settings.google_search_engine_id
        )
    except Exception as e:
        logger.warning(f"Failed to initialize Google Search verifier: {e}")

# Initialize services
document_processor = DocumentProcessor()
resume_analyzer = ResumeAuthenticityAnalyzer(
    google_search_verifier=google_search_verifier,
    use_selenium=settings.use_selenium_verification if hasattr(settings, 'use_selenium_verification') else False
)
jd_matcher = JDMatcher()
vetting_session = VettingSession()
resume_data_extractor = ResumeDataExtractor()

@router.post("/scan")
async def scan_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    Scan a single resume for authenticity without saving to database
    
    Args:
        file: Resume file to scan
        job_description: Optional job description for matching
        session_id: Vetting session ID
    
    Returns:
        Scan results with authenticity scores
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Save to temp location
        temp_dir = "temp/vetting_files"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"{file_hash}_{file.filename}")
        
        async with aiofiles.open(temp_file_path, 'wb') as f:
            await f.write(content)
        
        # Extract text from resume
        extracted_text = document_processor.extract_text(temp_file_path)
        
        # Analyze document structure (CRITICAL: same as upload page)
        structure_info = document_processor.analyze_document_structure(temp_file_path)
        
        # Extract candidate information for Google verification (CRITICAL: same as upload page)
        candidate_name = None
        candidate_email = None
        candidate_phone = None
        extracted_data = None
        try:
            extracted_data = resume_data_extractor.extract_all(extracted_text)
            if extracted_data:
                candidate_name = extracted_data.get('name')
                candidate_email = extracted_data.get('email')
                candidate_phone = extracted_data.get('phone')
        except Exception as e:
            logger.warning(f"Failed to extract candidate data: {str(e)}")
        
        # Analyze authenticity (SAME as upload page with all parameters)
        authenticity_result = resume_analyzer.analyze_authenticity(
            text_content=extracted_text,
            structure_info=structure_info,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone
        )
        
        # JD matching if job description provided
        matching_result = None
        if job_description:
            matching_result = jd_matcher.match(extracted_text, job_description)
        
        # Build scan result (INCLUDE extracted_data for later use)
        scan_result = {
            "filename": file.filename,
            "file_hash": file_hash,
            "file_size": len(content),
            "authenticity_score": authenticity_result,
            "matching_score": matching_result,
            "extracted_text_length": len(extracted_text),
            "extracted_text": extracted_text,  # Store for database upload
            "extracted_data": extracted_data   # Store candidate info for database upload
        }
        
        # Store in vetting session
        vetting_session.store_scan_result(
            session_id=session_id,
            file_hash=file_hash,
            file_name=file.filename,
            scan_result=scan_result
        )
        
        logger.info(f"Scanned resume: {file.filename} (Session: {session_id})")
        
        return {
            "session_id": session_id,
            "file_hash": file_hash,
            "scan_result": scan_result,
            "status": "scanned"
        }
        
    except Exception as e:
        logger.error(f"Error scanning resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/batch-scan")
async def batch_scan_resumes(
    files: List[UploadFile] = File(...),
    job_description: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    Scan multiple resumes for authenticity without saving to database
    
    Args:
        files: List of resume files to scan
        job_description: Optional job description for matching
        session_id: Vetting session ID
    
    Returns:
        Batch scan results
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Validate file count
        if len(files) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 files allowed")
        
        results = []
        errors = []
        
        for file in files:
            try:
                # Scan individual file
                result = await scan_resume(file, job_description, session_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Error scanning {file.filename}: {str(e)}")
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "session_id": session_id,
            "total_scanned": len(results),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch scan failed: {str(e)}")


@router.get("/session/{session_id}")
def get_session(session_id: str):
    """Get vetting session data"""
    try:
        session_data = vetting_session.get_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/resumes")
def get_scanned_resumes(session_id: str):
    """Get all scanned resumes in a session"""
    try:
        resumes = vetting_session.get_scanned_resumes(session_id)
        return {
            "session_id": session_id,
            "total": len(resumes),
            "resumes": resumes
        }
        
    except Exception as e:
        logger.error(f"Error retrieving scanned resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/approve/{file_hash}")
def approve_resume(session_id: str, file_hash: str):
    """Mark a resume as approved"""
    try:
        success = vetting_session.mark_approved(session_id, file_hash)
        
        if not success:
            raise HTTPException(status_code=404, detail="Resume not found in session")
        
        return {"status": "approved", "file_hash": file_hash}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/reject/{file_hash}")
def reject_resume(session_id: str, file_hash: str):
    """Mark a resume as rejected"""
    try:
        success = vetting_session.mark_rejected(session_id, file_hash)
        
        if not success:
            raise HTTPException(status_code=404, detail="Resume not found in session")
        
        return {"status": "rejected", "file_hash": file_hash}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/bulk-approve")
def bulk_approve(session_id: str, min_score: float = 70.0):
    """Bulk approve resumes with score >= min_score"""
    try:
        approved_count = vetting_session.bulk_approve_by_score(session_id, min_score)
        
        return {
            "approved_count": approved_count,
            "min_score": min_score
        }
        
    except Exception as e:
        logger.error(f"Error bulk approving: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/approved")
def get_approved_resumes(session_id: str):
    """Get approved resumes from session"""
    try:
        approved = vetting_session.get_approved_resumes(session_id)
        
        return {
            "session_id": session_id,
            "total_approved": len(approved),
            "approved_resumes": approved
        }
        
    except Exception as e:
        logger.error(f"Error retrieving approved resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear/delete a vetting session"""
    try:
        success = vetting_session.clear_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"status": "cleared", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/upload-approved")
async def upload_approved_to_database(session_id: str, db: Session = Depends(get_db)):
    """
    Upload approved resumes from vetting session to the database
    
    Args:
        session_id: Vetting session ID
        db: Database session
    
    Returns:
        Summary of uploaded resumes
    """
    from tasks.resume_tasks import process_resume
    from models.database import Resume, Candidate
    import shutil
    
    try:
        # Get approved resumes from session
        approved_resumes = vetting_session.get_approved_resumes(session_id)
        
        if not approved_resumes:
            raise HTTPException(status_code=404, detail="No approved resumes found in session")
        
        uploaded = []
        failed = []
        
        for resume_data in approved_resumes:
            try:
                file_hash = resume_data['file_hash']
                file_name = resume_data['file_name']
                
                # Check if already in database
                from sqlalchemy import select
                stmt = select(Resume).filter(Resume.file_hash == file_hash)
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    failed.append({
                        "file_name": file_name,
                        "reason": "Already in database",
                        "status": "duplicate"
                    })
                    continue
                
                # Copy file from temp to permanent storage
                temp_file_path = os.path.join("temp/vetting_files", f"{file_hash}_{file_name}")
                
                if not os.path.exists(temp_file_path):
                    failed.append({
                        "file_name": file_name,
                        "reason": "Temp file not found",
                        "status": "error"
                    })
                    continue
                
                permanent_file_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}_{file_name}")
                shutil.copy2(temp_file_path, permanent_file_path)
                
                # Get extracted data from scan result
                scan_result = resume_data.get('scan_result', {})
                extracted_text = scan_result.get('extracted_text', '')
                extracted_data = scan_result.get('extracted_data', {})
                
                # Extract candidate information from parsed data
                candidate_name = extracted_data.get('name', 'Unknown Candidate')
                candidate_email = extracted_data.get('email')
                candidate_phone = extracted_data.get('phone')
                
                # Check if candidate already exists by email
                candidate = None
                if candidate_email:
                    from sqlalchemy import select
                    stmt = select(Candidate).filter(Candidate.email == candidate_email)
                    result = await db.execute(stmt)
                    candidate = result.scalar_one_or_none()
                
                # Create new candidate if doesn't exist
                if not candidate:
                    candidate = Candidate(
                        full_name=candidate_name,
                        email=candidate_email,
                        phone=candidate_phone,
                        source="vetting",
                        status="new",
                        created_by="system"
                    )
                    db.add(candidate)
                    await db.commit()
                    await db.refresh(candidate)
                    logger.info(f"Created new candidate: {candidate_name} (ID: {candidate.id})")
                
                # Create resume record with extracted data
                # Get file info
                file_size = os.path.getsize(permanent_file_path)
                file_ext = os.path.splitext(file_name)[1].lower().replace('.', '')
                
                resume = Resume(
                    file_name=file_name,
                    original_file_name=file_name,
                    file_path=permanent_file_path,
                    file_size=file_size,
                    file_type=file_ext,
                    file_hash=file_hash,
                    mime_type=f"application/{file_ext}",
                    status="uploaded",
                    processing_status="pending",
                    extracted_text=extracted_text,
                    parsed_data=extracted_data,
                    uploaded_by="system",  # For MVP, use system user
                    candidate_id=candidate.id,  # Link to candidate
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    candidate_phone=candidate_phone
                )
                db.add(resume)
                await db.commit()
                await db.refresh(resume)
                
                # Trigger background processing
                process_resume.delay(resume.id)
                
                uploaded.append({
                    "file_name": file_name,
                    "resume_id": resume.id,
                    "status": "processing"
                })
                
                logger.info(f"Uploaded approved resume: {file_name} (ID: {resume.id})")
                
            except Exception as e:
                logger.error(f"Error uploading {resume_data.get('file_name')}: {str(e)}")
                failed.append({
                    "file_name": resume_data.get('file_name'),
                    "reason": str(e),
                    "status": "error"
                })
                await db.rollback()
        
        return {
            "session_id": session_id,
            "total_approved": len(approved_resumes),
            "uploaded": len(uploaded),
            "failed": len(failed),
            "uploaded_resumes": uploaded,
            "failed_resumes": failed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading approved resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
