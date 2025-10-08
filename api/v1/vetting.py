"""
Resume Vetting API
Endpoints for scanning resumes without saving to database
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
import hashlib
import uuid
import os
import aiofiles

from services.document_processor import DocumentProcessor
from services.resume_analyzer import ResumeAuthenticityAnalyzer
from services.jd_matcher import JDMatcher
from services.vetting_session import VettingSession
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
document_processor = DocumentProcessor()
resume_analyzer = ResumeAuthenticityAnalyzer()
jd_matcher = JDMatcher()
vetting_session = VettingSession()

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
        
        # Analyze authenticity
        authenticity_result = resume_analyzer.analyze(extracted_text)
        
        # JD matching if job description provided
        matching_result = None
        if job_description:
            matching_result = jd_matcher.match(extracted_text, job_description)
        
        # Build scan result
        scan_result = {
            "filename": file.filename,
            "file_hash": file_hash,
            "file_size": len(content),
            "authenticity_score": authenticity_result,
            "matching_score": matching_result,
            "extracted_text_length": len(extracted_text)
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
