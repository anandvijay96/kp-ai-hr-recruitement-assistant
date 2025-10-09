from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import os
import uuid
import aiofiles
from datetime import datetime

from core.database import get_db
from core.config import settings
from models.resume_models import ResumeUploadResponse, JobStatusResponse
from models.db import Resume, Candidate
from services.duplicate_detector import DuplicateDetector
from services.candidate_service import CandidateService
from services.resume_service import ResumeService

router = APIRouter()
logger = logging.getLogger(__name__)

# Services that don't need database session can be instantiated globally
duplicate_detector = DuplicateDetector()

# Services that need database session (CandidateService, ResumeService) 
# will be instantiated in endpoint functions via dependency injection

# Create uploads directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a single resume for processing"""
    from tasks.resume_tasks import process_resume
    import hashlib
    
    try:
        # Read file content
        content = await file.read()
        
        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Check for duplicate file
        existing_resume = db.query(Resume).filter(Resume.file_hash == file_hash).first()
        if existing_resume:
            return ResumeUploadResponse(
                job_id=f"duplicate-{existing_resume.id}",
                file_name=file.filename,
                status="duplicate",
                message=f"This file was already uploaded as {existing_resume.file_name}"
            )
        
        # Save file
        file_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}_{file.filename}")
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create resume record
        resume = Resume(
            file_name=file.filename,
            file_path=file_path,
            file_hash=file_hash,
            upload_status="pending"
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        # Trigger background processing
        process_resume.delay(resume.id)
        
        logger.info(f"Resume uploaded: {file.filename} (ID: {resume.id})")
        
        return ResumeUploadResponse(
            job_id=str(resume.id),
            file_name=file.filename,
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/bulk-upload")
async def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload multiple resumes (up to 50) for batch processing.
    
    Returns:
        - batch_id: Unique identifier for this batch
        - total_files: Number of files in batch
        - accepted: List of files accepted for processing
        - rejected: List of files rejected (duplicates, errors)
        - status: Overall batch status
    """
    from tasks.resume_tasks import process_resume
    import hashlib
    
    MAX_FILES = 50
    
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {MAX_FILES} files allowed per batch. You uploaded {len(files)} files."
        )
    
    batch_id = str(uuid.uuid4())
    accepted = []
    rejected = []
    
    try:
        for file in files:
            try:
                # Read file content
                content = await file.read()
                
                # Validate file size (max 10MB)
                if len(content) > 10 * 1024 * 1024:
                    rejected.append({
                        "file_name": file.filename,
                        "reason": "File too large (max 10MB)",
                        "status": "rejected"
                    })
                    continue
                
                # Calculate file hash
                file_hash = hashlib.sha256(content).hexdigest()
                
                # Check for duplicate file
                existing_resume = db.query(Resume).filter(Resume.file_hash == file_hash).first()
                if existing_resume:
                    rejected.append({
                        "file_name": file.filename,
                        "reason": f"Duplicate of {existing_resume.file_name}",
                        "status": "duplicate",
                        "existing_resume_id": existing_resume.id
                    })
                    continue
                
                # Save file
                file_path = os.path.join(
                    settings.upload_dir, 
                    f"batch_{batch_id}_{uuid.uuid4()}_{file.filename}"
                )
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
                
                # Create resume record
                resume = Resume(
                    file_name=file.filename,
                    file_path=file_path,
                    file_hash=file_hash,
                    upload_status="pending"
                )
                db.add(resume)
                db.flush()  # Get resume ID without committing
                
                # Trigger background processing
                process_resume.delay(resume.id)
                
                accepted.append({
                    "file_name": file.filename,
                    "resume_id": resume.id,
                    "status": "queued",
                    "job_id": str(resume.id)
                })
                
                logger.info(f"Batch {batch_id}: Queued {file.filename} (ID: {resume.id})")
                
            except Exception as file_error:
                logger.error(f"Error processing file {file.filename}: {str(file_error)}")
                rejected.append({
                    "file_name": file.filename,
                    "reason": str(file_error),
                    "status": "error"
                })
        
        # Commit all accepted resumes
        db.commit()
        
        return {
            "batch_id": batch_id,
            "total_files": len(files),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "accepted": accepted,
            "rejected": rejected,
            "status": "processing" if accepted else "failed",
            "message": f"Accepted {len(accepted)}/{len(files)} files for processing"
        }
        
    except Exception as e:
        logger.error(f"Bulk upload error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


@router.get("/batch-status/{batch_id}")
async def get_batch_status(batch_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get status of a batch upload by searching for resumes with batch_id in file_path.
    
    Returns:
        - batch_id: Batch identifier
        - total_resumes: Total resumes in batch
        - completed: Number of completed resumes
        - processing: Number still processing
        - failed: Number of failed resumes
        - resumes: List of resume statuses
    """
    try:
        # Find all resumes from this batch
        resumes = db.query(Resume).filter(
            Resume.file_path.like(f"%batch_{batch_id}%")
        ).all()
        
        if not resumes:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
        
        completed = sum(1 for r in resumes if r.upload_status == "completed")
        processing = sum(1 for r in resumes if r.upload_status in ["pending", "processing"])
        failed = sum(1 for r in resumes if r.upload_status == "failed")
        
        resume_statuses = [
            {
                "resume_id": r.id,
                "file_name": r.file_name,
                "status": r.upload_status,
                "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
                "candidate_id": r.candidate_id,
                "authenticity_score": r.authenticity_score
            }
            for r in resumes
        ]
        
        return {
            "batch_id": batch_id,
            "total_resumes": len(resumes),
            "completed": completed,
            "processing": processing,
            "failed": failed,
            "progress_percentage": round((completed / len(resumes)) * 100, 1) if resumes else 0,
            "status": "completed" if completed == len(resumes) else "processing",
            "resumes": resume_statuses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get status of a resume processing job"""
    try:
        resume_id = int(job_id)
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        result = None
        if resume.upload_status == "completed":
            result = {
                "resume_id": resume.id,
                "file_name": resume.file_name,
                "candidate_id": resume.candidate_id,
                "authenticity_score": resume.authenticity_score,
                "processed_at": resume.processed_at.isoformat() if resume.processed_at else None
            }
        
        return JobStatusResponse(
            job_id=job_id,
            status=resume.upload_status,
            result=result
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
