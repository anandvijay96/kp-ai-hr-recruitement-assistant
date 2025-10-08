"""Service layer for job management business logic"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from typing import Optional, List, Dict
from datetime import datetime
import logging
import json

from models.database import Job, JobSkill, JobDocument, JobRecruiter, JobStatusHistory, Skill, User
from models.job_schemas import (
    JobCreateRequest, JobUpdateRequest, RecruiterAssignmentModel
)

logger = logging.getLogger(__name__)


class JobService:
    """Service for job management operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    # ========================================================================
    # CREATE OPERATIONS
    # ========================================================================
    
    async def create_job(
        self,
        job_data: JobCreateRequest,
        created_by: str
    ) -> dict:
        """
        Create a new job requisition
        
        Args:
            job_data: Job creation request data
            created_by: User ID creating the job
        
        Returns:
            Created job details
        """
        try:
            # Create job record
            job = Job(
                title=job_data.title,
                department=job_data.department,
                location_city=job_data.location.city,
                location_state=job_data.location.state,
                location_country=job_data.location.country,
                is_remote=job_data.location.is_remote,
                work_type=job_data.work_type.value,
                employment_type=job_data.employment_type.value,
                num_openings=job_data.num_openings,
                description=job_data.description,
                responsibilities=json.dumps(job_data.responsibilities),
                mandatory_requirements=json.dumps(job_data.requirements.mandatory),
                preferred_requirements=json.dumps(job_data.requirements.preferred),
                education_requirement=job_data.education_requirement,
                certifications=json.dumps(job_data.certifications),
                status=job_data.status.value,
                closing_date=job_data.closing_date.isoformat() if job_data.closing_date else None,
                created_by=created_by,
                template_id=job_data.template_id
            )
            
            # Add salary if provided
            if job_data.salary_range:
                job.salary_min = str(job_data.salary_range.min) if job_data.salary_range.min else None
                job.salary_max = str(job_data.salary_range.max) if job_data.salary_range.max else None
                job.salary_currency = job_data.salary_range.currency
                job.salary_period = job_data.salary_range.period
            
            # Build search text
            job.search_text = self._build_search_text(job)
            
            self.db.add(job)
            await self.db.flush()
            
            # Add skills
            if job_data.skills:
                await self._add_job_skills(job.id, job_data.skills)
            
            # Assign recruiters
            if job_data.assigned_recruiters:
                await self._assign_recruiters_internal(
                    job.id,
                    job_data.assigned_recruiters,
                    created_by
                )
            
            # If published, set published_at
            if job_data.status.value == "open":
                job.published_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Return job details
            return await self.get_job_by_id(job.id, include_relations=True)
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job: {str(e)}", exc_info=True)
            raise
    
    async def _add_job_skills(self, job_id: str, skills: List) -> None:
        """Add skills to a job"""
        for skill_data in skills:
            # Get or create skill
            skill_id = skill_data.skill_id
            if not skill_id:
                # Create new skill if doesn't exist
                result = await self.db.execute(
                    select(Skill).where(Skill.name == skill_data.name)
                )
                skill = result.scalar_one_or_none()
                
                if not skill:
                    skill = Skill(name=skill_data.name)
                    self.db.add(skill)
                    await self.db.flush()
                
                skill_id = skill.id
            
            # Create job-skill relationship
            job_skill = JobSkill(
                job_id=job_id,
                skill_id=skill_id,
                is_mandatory=skill_data.is_mandatory,
                proficiency_level=skill_data.proficiency_level.value,
                years_required=skill_data.years_required
            )
            self.db.add(job_skill)
    
    async def _assign_recruiters_internal(
        self,
        job_id: str,
        recruiters: List[RecruiterAssignmentModel],
        assigned_by: str
    ) -> None:
        """Internal method to assign recruiters"""
        for recruiter in recruiters:
            job_recruiter = JobRecruiter(
                job_id=job_id,
                user_id=recruiter.user_id,
                is_primary=recruiter.is_primary,
                assigned_by=assigned_by
            )
            self.db.add(job_recruiter)
    
    def _build_search_text(self, job: Job) -> str:
        """Build searchable text from job fields"""
        parts = [
            job.title or "",
            job.department or "",
            job.description or "",
            job.location_city or "",
            job.location_state or ""
        ]
        return " ".join(parts).lower()
    
    # ========================================================================
    # READ OPERATIONS
    # ========================================================================
    
    async def get_job_by_id(
        self,
        job_id: str,
        include_relations: bool = False
    ) -> Optional[dict]:
        """
        Get job by ID
        
        Args:
            job_id: Job UUID
            include_relations: Include skills, recruiters, documents
        
        Returns:
            Job details or None
        """
        try:
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return None
            
            job_dict = self._job_to_dict(job)
            
            if include_relations:
                # Get creator info
                creator_result = await self.db.execute(
                    select(User).where(User.id == job.created_by)
                )
                creator = creator_result.scalar_one_or_none()
                if creator:
                    job_dict["created_by"] = {
                        "id": creator.id,
                        "full_name": creator.full_name,
                        "email": creator.email
                    }
                
                # Get skills
                job_dict["skills"] = await self._get_job_skills(job_id)
                
                # Get recruiters
                job_dict["assigned_recruiters"] = await self._get_job_recruiters(job_id)
                
                # Get documents
                job_dict["documents"] = await self._get_job_documents(job_id)
                
                # Get application count (placeholder)
                job_dict["total_applications"] = 0
            
            return job_dict
        
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            raise
    
    async def search_jobs(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        department: Optional[str] = None,
        work_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> dict:
        """
        Search jobs with filters and pagination
        
        Args:
            search: Search term
            status: Filter by status
            department: Filter by department
            work_type: Filter by work type
            page: Page number
            limit: Items per page
            user_id: Current user ID
            user_role: Current user role
        
        Returns:
            Paginated job list
        """
        try:
            # Build query
            query = select(Job)
            
            # Apply filters
            conditions = []
            
            if search:
                search_term = f"%{search.lower()}%"
                conditions.append(Job.search_text.like(search_term))
            
            if status:
                conditions.append(Job.status == status)
            
            if department:
                conditions.append(Job.department == department)
            
            if work_type:
                conditions.append(Job.work_type == work_type)
            
            # Role-based filtering
            if user_role == "recruiter":
                # Recruiters only see jobs assigned to them or open jobs
                conditions.append(
                    or_(
                        Job.status == "open",
                        Job.id.in_(
                            select(JobRecruiter.job_id).where(
                                JobRecruiter.user_id == user_id
                            )
                        )
                    )
                )
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(Job)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit).order_by(Job.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            jobs = result.scalars().all()
            
            # Convert to dict
            jobs_list = [self._job_to_summary_dict(job) for job in jobs]
            
            # Calculate total pages
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            
            return {
                "jobs": jobs_list,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
        
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            raise
    
    async def _get_job_skills(self, job_id: str) -> List[dict]:
        """Get skills for a job"""
        result = await self.db.execute(
            select(JobSkill, Skill)
            .join(Skill, JobSkill.skill_id == Skill.id)
            .where(JobSkill.job_id == job_id)
        )
        
        skills = []
        for job_skill, skill in result.all():
            skills.append({
                "skill_id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "is_mandatory": job_skill.is_mandatory,
                "proficiency_level": job_skill.proficiency_level,
                "years_required": job_skill.years_required
            })
        
        return skills
    
    async def _get_job_recruiters(self, job_id: str) -> List[dict]:
        """Get recruiters assigned to a job"""
        result = await self.db.execute(
            select(JobRecruiter, User)
            .join(User, JobRecruiter.user_id == User.id)
            .where(
                and_(
                    JobRecruiter.job_id == job_id,
                    JobRecruiter.removed_at.is_(None)
                )
            )
        )
        
        recruiters = []
        for job_recruiter, user in result.all():
            recruiters.append({
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "is_primary": job_recruiter.is_primary,
                "assigned_at": job_recruiter.assigned_at.isoformat()
            })
        
        return recruiters
    
    async def _get_job_documents(self, job_id: str) -> List[dict]:
        """Get documents for a job"""
        result = await self.db.execute(
            select(JobDocument)
            .where(
                and_(
                    JobDocument.job_id == job_id,
                    JobDocument.deleted_at.is_(None)
                )
            )
        )
        
        documents = []
        for doc in result.scalars().all():
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "document_type": doc.document_type,
                "uploaded_at": doc.uploaded_at.isoformat()
            })
        
        return documents
    
    def _job_to_dict(self, job: Job) -> dict:
        """Convert Job model to dictionary"""
        return {
            "id": job.id,
            "uuid": job.uuid,
            "title": job.title,
            "department": job.department,
            "location_city": job.location_city,
            "location_state": job.location_state,
            "location_country": job.location_country,
            "is_remote": job.is_remote,
            "work_type": job.work_type,
            "employment_type": job.employment_type,
            "num_openings": job.num_openings,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "salary_period": job.salary_period,
            "description": job.description,
            "responsibilities": json.loads(job.responsibilities) if job.responsibilities else [],
            "mandatory_requirements": json.loads(job.mandatory_requirements) if job.mandatory_requirements else [],
            "preferred_requirements": json.loads(job.preferred_requirements) if job.preferred_requirements else [],
            "education_requirement": job.education_requirement,
            "certifications": json.loads(job.certifications) if job.certifications else [],
            "status": job.status,
            "published_at": job.published_at.isoformat() if job.published_at else None,
            "closing_date": job.closing_date,
            "closed_at": job.closed_at.isoformat() if job.closed_at else None,
            "close_reason": job.close_reason,
            "created_by": {"id": job.created_by},
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "template_id": job.template_id,
            "cloned_from_job_id": job.cloned_from_job_id
        }
    
    def _job_to_summary_dict(self, job: Job) -> dict:
        """Convert Job model to summary dictionary"""
        return {
            "id": job.id,
            "uuid": job.uuid,
            "title": job.title,
            "department": job.department,
            "location_city": job.location_city,
            "location_state": job.location_state,
            "work_type": job.work_type,
            "employment_type": job.employment_type,
            "num_openings": job.num_openings,
            "status": job.status,
            "published_at": job.published_at.isoformat() if job.published_at else None,
            "closing_date": job.closing_date,
            "created_at": job.created_at.isoformat()
        }
    
    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================
    
    async def update_job(
        self,
        job_id: str,
        update_data: JobUpdateRequest
    ) -> dict:
        """
        Update job information
        
        Args:
            job_id: Job UUID
            update_data: Fields to update
        
        Returns:
            Updated job details
        """
        try:
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            
            for field, value in update_dict.items():
                if field == "location" and value:
                    # value is a dict after model_dump()
                    job.location_city = value.get('city')
                    job.location_state = value.get('state')
                    job.location_country = value.get('country', 'USA')
                    job.is_remote = value.get('is_remote', False)
                elif field == "salary_range" and value:
                    # value is a dict after model_dump()
                    job.salary_min = str(value['min']) if value.get('min') else None
                    job.salary_max = str(value['max']) if value.get('max') else None
                    job.salary_currency = value.get('currency', 'USD')
                    job.salary_period = value.get('period', 'annual')
                elif field == "requirements" and value:
                    # value is a dict after model_dump()
                    job.mandatory_requirements = json.dumps(value.get('mandatory', []))
                    job.preferred_requirements = json.dumps(value.get('preferred', []))
                elif field == "responsibilities" and value:
                    job.responsibilities = json.dumps(value)
                elif field == "certifications" and value:
                    job.certifications = json.dumps(value)
                elif field == "skills" and value:
                    # Update skills separately
                    await self._update_job_skills(job_id, value)
                elif field == "work_type" and value:
                    # value might be a string or enum
                    job.work_type = value if isinstance(value, str) else value.value
                elif field == "employment_type" and value:
                    # value might be a string or enum
                    job.employment_type = value if isinstance(value, str) else value.value
                elif field == "closing_date" and value:
                    # value might be a string or date object
                    job.closing_date = value if isinstance(value, str) else value.isoformat()
                elif hasattr(job, field):
                    setattr(job, field, value)
            
            job.updated_at = datetime.utcnow()
            job.search_text = self._build_search_text(job)
            
            await self.db.commit()
            
            return await self.get_job_by_id(job_id, include_relations=True)
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job {job_id}: {str(e)}")
            raise
    
    async def _update_job_skills(self, job_id: str, skills: List) -> None:
        """Update job skills"""
        # Delete existing skills
        await self.db.execute(
            delete(JobSkill).where(JobSkill.job_id == job_id)
        )
        
        # Add new skills
        await self._add_job_skills(job_id, skills)
    
    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================
    
    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job (only drafts)
        
        Args:
            job_id: Job UUID
        
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return False
            
            if job.status != "draft":
                raise ValueError("Only draft jobs can be deleted")
            
            await self.db.delete(job)
            await self.db.commit()
            
            return True
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            raise
    
    # ========================================================================
    # WORKFLOW OPERATIONS
    # ========================================================================
    
    async def publish_job(
        self,
        job_id: str,
        published_by: str,
        send_notifications: bool = True
    ) -> dict:
        """
        Publish a draft job
        
        Args:
            job_id: Job UUID
            published_by: User ID publishing the job
            send_notifications: Send email notifications
        
        Returns:
            Updated job details
        """
        try:
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            if job.status != "draft":
                raise ValueError("Only draft jobs can be published")
            
            # Update status
            job.status = "open"
            job.published_at = datetime.utcnow()
            
            # Record status change
            await self._record_status_change(
                job_id, "draft", "open", "Published", published_by
            )
            
            await self.db.commit()
            
            # TODO: Send notifications if send_notifications is True
            
            return await self.get_job_by_id(job_id, include_relations=True)
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error publishing job {job_id}: {str(e)}")
            raise
    
    async def close_job(
        self,
        job_id: str,
        close_reason: str,
        notes: Optional[str],
        closed_by: str
    ) -> dict:
        """
        Close a job
        
        Args:
            job_id: Job UUID
            close_reason: Reason for closing
            notes: Additional notes
            closed_by: User ID closing the job
        
        Returns:
            Updated job details
        """
        try:
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            if job.status == "closed":
                raise ValueError("Job is already closed")
            
            old_status = job.status
            job.status = "closed"
            job.closed_at = datetime.utcnow()
            # Store the user's notes as the close reason, not the enum
            job.close_reason = notes if notes else close_reason
            
            # Record status change
            await self._record_status_change(
                job_id, old_status, "closed", notes or close_reason, closed_by
            )
            
            await self.db.commit()
            
            return await self.get_job_by_id(job_id, include_relations=True)
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error closing job {job_id}: {str(e)}")
            raise
    
    async def reopen_job(
        self,
        job_id: str,
        reopened_by: str
    ) -> dict:
        """
        Reopen a closed or on-hold job
        
        Args:
            job_id: Job UUID
            reopened_by: User ID reopening the job
        
        Returns:
            Updated job details
        """
        try:
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            if job.status not in ["closed", "on_hold"]:
                raise ValueError("Only closed or on-hold jobs can be reopened")
            
            old_status = job.status
            job.status = "open"
            job.closed_at = None
            job.close_reason = None
            
            # Record status change
            await self._record_status_change(
                job_id, old_status, "open", "Reopened", reopened_by
            )
            
            await self.db.commit()
            
            return await self.get_job_by_id(job_id, include_relations=True)
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error reopening job {job_id}: {str(e)}")
            raise
    
    async def _record_status_change(
        self,
        job_id: str,
        from_status: str,
        to_status: str,
        reason: str,
        changed_by: str
    ) -> None:
        """Record job status change in history"""
        history = JobStatusHistory(
            job_id=job_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            changed_by=changed_by
        )
        self.db.add(history)
    
    # ========================================================================
    # CLONING
    # ========================================================================
    
    async def clone_job(
        self,
        job_id: str,
        new_title: Optional[str],
        modify_fields: Optional[dict],
        created_by: str
    ) -> dict:
        """
        Clone an existing job
        
        Args:
            job_id: Job UUID to clone
            new_title: Optional new title
            modify_fields: Optional fields to modify
            created_by: User ID creating the clone
        
        Returns:
            Cloned job details
        """
        try:
            # Get original job
            original_job = await self.get_job_by_id(job_id, include_relations=True)
            
            if not original_job:
                raise ValueError("Job not found")
            
            # Create new job with same data
            new_job = Job(
                title=new_title or f"{original_job['title']} (Copy)",
                department=original_job["department"],
                location_city=original_job["location_city"],
                location_state=original_job["location_state"],
                location_country=original_job["location_country"],
                is_remote=original_job["is_remote"],
                work_type=original_job["work_type"],
                employment_type=original_job["employment_type"],
                num_openings=original_job["num_openings"],
                salary_min=original_job["salary_min"],
                salary_max=original_job["salary_max"],
                salary_currency=original_job["salary_currency"],
                salary_period=original_job["salary_period"],
                description=original_job["description"],
                responsibilities=json.dumps(original_job["responsibilities"]),
                mandatory_requirements=json.dumps(original_job["mandatory_requirements"]),
                preferred_requirements=json.dumps(original_job["preferred_requirements"]),
                education_requirement=original_job["education_requirement"],
                certifications=json.dumps(original_job["certifications"]),
                status="draft",  # Always start as draft
                created_by=created_by,
                cloned_from_job_id=job_id
            )
            
            # Apply modifications
            if modify_fields:
                for field, value in modify_fields.items():
                    if hasattr(new_job, field):
                        setattr(new_job, field, value)
            
            new_job.search_text = self._build_search_text(new_job)
            
            self.db.add(new_job)
            await self.db.flush()
            
            # Clone skills
            for skill in original_job["skills"]:
                job_skill = JobSkill(
                    job_id=new_job.id,
                    skill_id=skill["skill_id"],
                    is_mandatory=skill["is_mandatory"],
                    proficiency_level=skill["proficiency_level"],
                    years_required=skill["years_required"]
                )
                self.db.add(job_skill)
            
            await self.db.commit()
            
            return await self.get_job_by_id(new_job.id, include_relations=True)
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error cloning job {job_id}: {str(e)}")
            raise
    
    # ========================================================================
    # RECRUITER MANAGEMENT
    # ========================================================================
    
    async def assign_recruiters(
        self,
        job_id: str,
        recruiters: List[RecruiterAssignmentModel],
        assigned_by: str,
        send_notifications: bool = True
    ) -> dict:
        """
        Assign recruiters to a job
        
        Args:
            job_id: Job UUID
            recruiters: List of recruiter assignments
            assigned_by: User ID assigning recruiters
            send_notifications: Send email notifications
        
        Returns:
            Updated job details
        """
        try:
            # Verify job exists
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            # Validate only one primary recruiter
            primary_count = sum(1 for r in recruiters if r.is_primary)
            if primary_count > 1:
                raise ValueError("Only one primary recruiter allowed")
            
            # Remove existing assignments
            await self.db.execute(
                delete(JobRecruiter).where(JobRecruiter.job_id == job_id)
            )
            
            # Add new assignments
            await self._assign_recruiters_internal(job_id, recruiters, assigned_by)
            
            await self.db.commit()
            
            # TODO: Send notifications if send_notifications is True
            
            return await self.get_job_by_id(job_id, include_relations=True)
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assigning recruiters to job {job_id}: {str(e)}")
            raise
    
    async def remove_recruiter(
        self,
        job_id: str,
        user_id: str,
        removed_by: str
    ) -> None:
        """
        Remove a recruiter from a job
        
        Args:
            job_id: Job UUID
            user_id: User UUID to remove
            removed_by: User ID removing the recruiter
        """
        try:
            result = await self.db.execute(
                select(JobRecruiter).where(
                    and_(
                        JobRecruiter.job_id == job_id,
                        JobRecruiter.user_id == user_id
                    )
                )
            )
            job_recruiter = result.scalar_one_or_none()
            
            if not job_recruiter:
                raise ValueError("Recruiter assignment not found")
            
            job_recruiter.removed_at = datetime.utcnow()
            job_recruiter.removed_by = removed_by
            
            await self.db.commit()
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error removing recruiter from job {job_id}: {str(e)}")
            raise
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    async def get_statistics(
        self,
        user_id: str,
        user_role: str
    ) -> dict:
        """
        Get job statistics
        
        Args:
            user_id: Current user ID
            user_role: Current user role
        
        Returns:
            Statistics dictionary
        """
        try:
            # Total jobs
            total_result = await self.db.execute(
                select(func.count()).select_from(Job)
            )
            total = total_result.scalar()
            
            # By status
            status_result = await self.db.execute(
                select(Job.status, func.count())
                .group_by(Job.status)
            )
            by_status = {row[0]: row[1] for row in status_result.all()}
            
            # By department
            dept_result = await self.db.execute(
                select(Job.department, func.count())
                .where(Job.department.isnot(None))
                .group_by(Job.department)
            )
            by_department = {row[0]: row[1] for row in dept_result.all()}
            
            # By work type
            work_type_result = await self.db.execute(
                select(Job.work_type, func.count())
                .group_by(Job.work_type)
            )
            by_work_type = {row[0]: row[1] for row in work_type_result.all()}
            
            return {
                "total_jobs": total,
                "by_status": by_status,
                "by_department": by_department,
                "by_work_type": by_work_type
            }
        
        except Exception as e:
            logger.error(f"Error getting job statistics: {str(e)}")
            raise
