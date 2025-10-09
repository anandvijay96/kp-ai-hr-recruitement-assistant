"""Resume service for managing resume uploads and operations"""
from typing import Dict, List, Optional
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, delete
import logging

from models.database import Resume, ResumeUploadHistory, BulkUploadSession, User
from services.file_storage_service import FileStorageService
from services.file_validator_service import FileValidatorService
from services.resume_parser_service import ResumeParserService

logger = logging.getLogger(__name__)


class ResumeService:
    """Main service for resume operations"""
    
    def __init__(
        self,
        db_session: AsyncSession,
        file_storage: FileStorageService = None,
        file_validator: FileValidatorService = None,
        resume_parser: ResumeParserService = None
    ):
        self.db = db_session
        self.file_storage = file_storage or FileStorageService()
        self.file_validator = file_validator or FileValidatorService()
        self.resume_parser = resume_parser or ResumeParserService()
    
    async def upload_resume(
        self,
        file_content: bytes,
        file_name: str,
        uploaded_by: str,
        metadata: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict:
        """
        Upload a single resume
        
        Args:
            file_content: File binary content
            file_name: Original file name
            uploaded_by: User ID who uploaded
            metadata: Optional metadata (candidate_name, email, phone)
            ip_address: Upload IP address
            user_agent: User agent string
            
        Returns:
            Dict with resume details
            
        Raises:
            ValueError: If validation fails
        """
        try:
            metadata = metadata or {}
            
            # 1. Validate file
            is_valid, errors = self.file_validator.validate_file(file_content, file_name)
            if not is_valid:
                raise ValueError("; ".join(errors))
            
            # 2. Calculate file hash
            file_hash = self.file_validator.calculate_file_hash(file_content)
            
            # 3. Check for duplicates
            duplicate = await self._check_duplicate(file_hash)
            if duplicate:
                logger.warning(f"Duplicate resume detected: {file_hash}")
                return {
                    "is_duplicate": True,
                    "existing_resume": duplicate
                }
            
            # 4. Generate file path and save
            resume_id = str(uuid.uuid4())
            file_ext = self.file_validator.get_file_extension(file_name).lstrip('.')
            file_path = self.file_storage.generate_file_path(uploaded_by, resume_id, file_ext)
            
            await self.file_storage.save_file(file_content, file_path)
            
            # 5. Parse resume to extract data (with error handling)
            parsed_data = {}
            try:
                logger.info(f"Parsing resume: {resume_id}")
                parsed_data = await self.resume_parser.parse_resume(file_content, file_ext, file_path)
                
                # Update metadata with parsed data if not provided
                if not metadata.get("candidate_name") and parsed_data.get("name"):
                    metadata["candidate_name"] = parsed_data["name"]
                if not metadata.get("candidate_email") and parsed_data.get("email"):
                    metadata["candidate_email"] = parsed_data["email"]
                if not metadata.get("candidate_phone") and parsed_data.get("phone"):
                    metadata["candidate_phone"] = parsed_data["phone"]
                    
                logger.info(f"Resume parsed successfully: {resume_id}")
            except Exception as parse_error:
                logger.warning(f"Failed to parse resume {resume_id}: {str(parse_error)}")
                # Continue with upload even if parsing fails
                parsed_data = {}
            
            # 6. Create database record
            resume = Resume(
                id=resume_id,
                file_name=f"{resume_id}.{file_ext}",
                original_file_name=self.file_validator.sanitize_filename(file_name),
                file_path=file_path,
                file_size=len(file_content),
                file_type=file_ext,
                file_hash=file_hash,
                mime_type=self.file_validator.get_mime_type(file_content, file_ext),
                candidate_name=metadata.get("candidate_name"),
                candidate_email=metadata.get("candidate_email"),
                candidate_phone=metadata.get("candidate_phone"),
                extracted_text=parsed_data.get("extracted_text"),
                parsed_data=parsed_data,  # Store all parsed data as JSON
                uploaded_by=uploaded_by,
                upload_ip=ip_address,
                upload_user_agent=user_agent,
                status="parsed" if parsed_data.get("name") else "uploaded",  # Mark as parsed if we got data
                virus_scan_status="clean"  # Simplified - no actual scanning for now
            )
            
            self.db.add(resume)
            
            # 6. Log upload history
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
            
            logger.info(f"Resume uploaded successfully: {resume_id} by user {uploaded_by}")
            
            return {
                "resume_id": resume_id,
                "file_name": file_name,
                "file_size": len(file_content),
                "file_type": file_ext,
                "upload_date": resume.upload_date,
                "virus_scan_status": "clean",
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
        """Check if file hash exists in database (excluding deleted resumes)"""
        result = await self.db.execute(
            select(Resume).where(
                and_(
                    Resume.file_hash == file_hash,
                    Resume.deleted_at.is_(None)  # Only check non-deleted resumes
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
        status: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: str = None,
        current_user_role: str = None
    ) -> Dict:
        """
        Get paginated list of resumes
        
        Args:
            page: Page number (1-indexed)
            limit: Items per page
            status: Filter by status
            uploaded_by: Filter by uploader
            search: Search term
            current_user_id: Current user ID
            current_user_role: Current user role
            
        Returns:
            Dict with resumes and pagination info
        """
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
            # Search only by candidate name
            query = query.where(Resume.candidate_name.ilike(search_pattern))
        
        # Get total count
        count_query = select(func.count()).select_from(Resume).where(Resume.deleted_at.is_(None))
        if status:
            count_query = count_query.where(Resume.status == status)
        if uploaded_by:
            count_query = count_query.where(Resume.uploaded_by == uploaded_by)
        elif current_user_role == "recruiter":
            count_query = count_query.where(Resume.uploaded_by == current_user_id)
        if search:
            search_pattern = f"%{search}%"
            # Search only by candidate name
            count_query = count_query.where(Resume.candidate_name.ilike(search_pattern))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit).order_by(Resume.upload_date.desc())
        
        # Execute query
        result = await self.db.execute(query)
        resumes = result.scalars().all()
        
        # Format resumes
        resume_list = []
        for resume in resumes:
            # Get uploader name
            uploader_result = await self.db.execute(
                select(User.full_name).where(User.id == resume.uploaded_by)
            )
            uploader_name = uploader_result.scalar_one_or_none() or "Unknown"
            
            resume_list.append({
                "id": resume.id,
                "file_name": resume.original_file_name,
                "candidate_name": resume.candidate_name,
                "candidate_email": resume.candidate_email,
                "upload_date": resume.upload_date,
                "uploaded_by_name": uploader_name,
                "status": resume.status,
                "file_size": resume.file_size,
                "virus_scan_status": resume.virus_scan_status
            })
        
        return {
            "resumes": resume_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0
            }
        }
    
    async def get_resume_by_id(
        self,
        resume_id: str,
        user_id: str,
        user_role: str
    ) -> Optional[Dict]:
        """
        Get resume details by ID
        
        Args:
            resume_id: Resume ID
            user_id: Current user ID
            user_role: Current user role
            
        Returns:
            Resume details or None
        """
        query = select(Resume).where(
            and_(
                Resume.id == resume_id,
                Resume.deleted_at.is_(None)
            )
        )
        
        # Recruiters can only see their own uploads
        if user_role == "recruiter":
            query = query.where(Resume.uploaded_by == user_id)
        
        result = await self.db.execute(query)
        resume = result.scalar_one_or_none()
        
        if not resume:
            return None
        
        # Get uploader details
        uploader_result = await self.db.execute(
            select(User).where(User.id == resume.uploaded_by)
        )
        uploader = uploader_result.scalar_one_or_none()
        
        return {
            "id": resume.id,
            "file_name": resume.file_name,
            "original_file_name": resume.original_file_name,
            "file_size": resume.file_size,
            "file_type": resume.file_type,
            "candidate_name": resume.candidate_name,
            "candidate_email": resume.candidate_email,
            "candidate_phone": resume.candidate_phone,
            "uploaded_by": {
                "id": uploader.id if uploader else None,
                "name": uploader.full_name if uploader else "Unknown",
                "email": uploader.email if uploader else None
            },
            "upload_date": resume.upload_date,
            "status": resume.status,
            "virus_scan_status": resume.virus_scan_status,
            "parsed_data": resume.parsed_data,
            "file_path": resume.file_path
        }
    
    async def delete_resume(
        self,
        resume_id: str,
        user_id: str,
        user_role: str
    ) -> bool:
        """
        Soft delete a resume
        
        Args:
            resume_id: Resume ID
            user_id: Current user ID
            user_role: Current user role
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If not authorized or resume not found
        """
        # Get resume
        query = select(Resume).where(
            and_(
                Resume.id == resume_id,
                Resume.deleted_at.is_(None)
            )
        )
        
        result = await self.db.execute(query)
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise ValueError("Resume not found")
        
        # Check permissions
        if user_role == "recruiter" and resume.uploaded_by != user_id:
            raise ValueError("You don't have permission to delete this resume")
        
        # Soft delete
        resume.deleted_at = datetime.utcnow()
        resume.deleted_by = user_id
        resume.status = "deleted"
        
        # Log action
        history = ResumeUploadHistory(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            action="deleted",
            performed_by=user_id,
            details={"reason": "user_requested"}
        )
        
        self.db.add(history)
        await self.db.commit()
        
        logger.info(f"Resume {resume_id} deleted by user {user_id}")
        
        return True
    
    async def create_bulk_upload_session(
        self,
        user_id: str,
        total_files: int
    ) -> Dict:
        """
        Create a bulk upload session
        
        Args:
            user_id: User ID
            total_files: Total number of files
            
        Returns:
            Session details
        """
        session = BulkUploadSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            total_files=total_files,
            status="in_progress"
        )
        
        self.db.add(session)
        await self.db.commit()
        
        logger.info(f"Bulk upload session created: {session.id} for user {user_id}")
        
        return {
            "session_id": session.id,
            "total_files": total_files,
            "status": "in_progress"
        }
    
    async def get_bulk_upload_status(
        self,
        session_id: str,
        user_id: str
    ) -> Dict:
        """
        Get bulk upload session status
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Session status
            
        Raises:
            ValueError: If session not found
        """
        result = await self.db.execute(
            select(BulkUploadSession).where(
                and_(
                    BulkUploadSession.id == session_id,
                    BulkUploadSession.user_id == user_id
                )
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError("Bulk upload session not found")
        
        progress_percentage = (session.processed_files / session.total_files * 100) if session.total_files > 0 else 0
        
        return {
            "session_id": session.id,
            "status": session.status,
            "total_files": session.total_files,
            "processed": session.processed_files,
            "successful": session.successful_uploads,
            "failed": session.failed_uploads,
            "duplicates": session.duplicate_files,
            "progress_percentage": round(progress_percentage, 2),
            "files": []  # TODO: Implement file-level tracking
        }
