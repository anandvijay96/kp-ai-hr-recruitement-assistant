from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session

from core.database import get_db
from services.resume_service import ResumeService
from models.resume_models import ResumeUploadResponse, JobStatusResponse

router = APIRouter()
resume_service = ResumeService()

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads a single resume for processing."""
    if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    result = resume_service.upload_resume(file, db)
    return result

@router.post("/upload-batch", response_model=List[ResumeUploadResponse])
async def upload_resume_batch(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Uploads a batch of resumes for processing."""
    for file in files:
        if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")
    results = resume_service.upload_resume_batch(files, db)
    return results

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Checks the status of a resume processing job."""
    status = resume_service.get_job_status(job_id, db)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status
