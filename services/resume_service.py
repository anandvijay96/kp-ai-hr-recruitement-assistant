import os
import hashlib
import logging
from typing import List, Dict, Any, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from datetime import datetime

from core.config import settings
from core.database import SessionLocal
from models.db import Resume, Candidate
from tasks.resume_tasks import process_resume

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for handling resume uploads and processing"""
    
    def __init__(self):
        self.upload_dir = settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def _save_file(self, file: UploadFile, content: bytes) -> str:
        """Save uploaded file and return file path"""
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(self.upload_dir, filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    def upload_resume(self, file: UploadFile, db: Session) -> Dict[str, Any]:
        """
        Handles single resume upload and initiates background processing.
        
        Args:
            file: Uploaded file
            db: Database session
            
        Returns:
            Dict with job_id, file_name, status
        """
        try:
            # Read file content
            content = file.file.read()
            file_hash = self._calculate_file_hash(content)
            
            # Check for duplicate by file hash
            existing_resume = db.query(Resume).filter(Resume.file_hash == file_hash).first()
            if existing_resume:
                logger.info(f"Duplicate resume detected: {file_hash}")
                return {
                    "job_id": str(existing_resume.id),
                    "file_name": file.filename,
                    "status": "duplicate",
                    "message": "This resume has already been uploaded",
                    "existing_resume_id": existing_resume.id
                }
            
            # Save file
            file_path = self._save_file(file, content)
            
            # Create Resume record in database
            resume = Resume(
                file_name=file.filename,
                file_path=file_path,
                file_hash=file_hash,
                upload_status='pending'
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)
            
            # Trigger background processing task
            process_resume.delay(resume.id)
            
            logger.info(f"Resume uploaded: {resume.id} - {file.filename}")
            
            return {
                "job_id": str(resume.id),
                "file_name": file.filename,
                "status": "processing"
            }
        
        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}", exc_info=True)
            db.rollback()
            raise
    
    def upload_resume_batch(self, files: List[UploadFile], db: Session) -> List[Dict[str, Any]]:
        """
        Handles batch resume uploads.
        
        Args:
            files: List of uploaded files
            db: Database session
            
        Returns:
            List of dicts with job_id, file_name, status for each file
        """
        results = []
        
        for file in files:
            try:
                result = self.upload_resume(file, db)
                results.append(result)
            except Exception as e:
                logger.error(f"Error uploading {file.filename}: {str(e)}")
                results.append({
                    "job_id": None,
                    "file_name": file.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def get_job_status(self, job_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Retrieves the status of a resume processing job.
        
        Args:
            job_id: Resume ID (job ID)
            db: Database session
            
        Returns:
            Dict with job status information
        """
        try:
            resume = db.query(Resume).filter(Resume.id == int(job_id)).first()
            
            if not resume:
                return None
            
            return {
                "job_id": str(resume.id),
                "file_name": resume.file_name,
                "status": resume.upload_status,
                "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
                "processed_at": resume.processed_at.isoformat() if resume.processed_at else None,
                "candidate_id": resume.candidate_id,
                "authenticity_score": resume.authenticity_score,
                "extracted_data": resume.extracted_data,
            }
        
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return None
    
    def get_resume_by_id(self, resume_id: int, db: Session) -> Optional[Resume]:
        """Get resume by ID"""
        return db.query(Resume).filter(Resume.id == resume_id).first()
    
    def get_candidate_resumes(self, candidate_id: int, db: Session) -> List[Resume]:
        """Get all resumes for a candidate"""
        return db.query(Resume).filter(Resume.candidate_id == candidate_id).all()
