"""Service for managing candidates and their related data"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
import uuid

from models.database import (
    Candidate, Education, WorkExperience, Skill, CandidateSkill,
    Certification, Resume
)
from models.candidate_schemas import (
    ParsedResumeData, CandidateCreate, CandidateUpdate,
    CandidateResponse, EducationResponse, WorkExperienceResponse,
    SkillResponse, CertificationResponse, CandidateListItem
)

logger = logging.getLogger(__name__)


class CandidateService:
    """Service for managing candidate records"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_candidate_from_parsed_data(
        self,
        parsed_data: ParsedResumeData,
        created_by: str,
        resume_id: Optional[str] = None
    ) -> str:
        """
        Create a candidate record from parsed resume data
        
        Args:
            parsed_data: Parsed resume data
            created_by: User ID who created the candidate
            resume_id: Optional resume ID to link
            
        Returns:
            Candidate ID
        """
        try:
            # Create candidate
            candidate = Candidate(
                id=str(uuid.uuid4()),
                uuid=str(uuid.uuid4()),
                full_name=parsed_data.personal_info.name,
                email=parsed_data.personal_info.email,
                phone=parsed_data.personal_info.phone,
                linkedin_url=parsed_data.personal_info.linkedin_url,
                location=parsed_data.personal_info.location,
                source="upload",
                status="new",
                created_by=created_by
            )
            self.db.add(candidate)
            await self.db.flush()  # Get candidate ID
            
            # Add education records
            for edu_data in parsed_data.education:
                education = Education(
                    id=str(uuid.uuid4()),
                    candidate_id=candidate.id,
                    degree=edu_data.degree,
                    field=edu_data.field,
                    institution=edu_data.institution,
                    location=edu_data.location,
                    start_date=edu_data.start_date,
                    end_date=edu_data.end_date,
                    gpa=edu_data.gpa,
                    confidence_score=str(edu_data.confidence) if edu_data.confidence else None
                )
                self.db.add(education)
            
            # Add work experience records
            for exp_data in parsed_data.experience:
                is_current = exp_data.end_date and exp_data.end_date.lower() in ['present', 'current']
                experience = WorkExperience(
                    id=str(uuid.uuid4()),
                    candidate_id=candidate.id,
                    company=exp_data.company,
                    title=exp_data.title,
                    location=exp_data.location,
                    start_date=exp_data.start_date,
                    end_date=exp_data.end_date if not is_current else None,
                    is_current=is_current,
                    duration_months=exp_data.duration_months,
                    description=exp_data.description,
                    confidence_score=str(exp_data.confidence) if exp_data.confidence else None
                )
                self.db.add(experience)
            
            # Add skills
            for skill_data in parsed_data.skills:
                # Check if skill exists
                result = await self.db.execute(
                    select(Skill).where(Skill.name == skill_data.name)
                )
                skill = result.scalar_one_or_none()
                
                if not skill:
                    # Create new skill
                    skill = Skill(
                        id=str(uuid.uuid4()),
                        name=skill_data.name,
                        category=skill_data.category
                    )
                    self.db.add(skill)
                    await self.db.flush()
                
                # Link skill to candidate
                candidate_skill = CandidateSkill(
                    candidate_id=candidate.id,
                    skill_id=skill.id,
                    proficiency=skill_data.proficiency,
                    confidence_score=str(skill_data.confidence) if skill_data.confidence else None
                )
                self.db.add(candidate_skill)
            
            # Add certifications
            for cert_data in parsed_data.certifications:
                certification = Certification(
                    id=str(uuid.uuid4()),
                    candidate_id=candidate.id,
                    name=cert_data.name,
                    issuer=cert_data.issuer,
                    issue_date=cert_data.date,
                    expiry_date=cert_data.expiry_date,
                    credential_id=cert_data.credential_id,
                    confidence_score=str(cert_data.confidence) if cert_data.confidence else None
                )
                self.db.add(certification)
            
            # Link resume if provided
            if resume_id:
                result = await self.db.execute(
                    select(Resume).where(Resume.id == resume_id)
                )
                resume = result.scalar_one_or_none()
                if resume:
                    resume.candidate_id = candidate.id
            
            await self.db.commit()
            logger.info(f"Created candidate {candidate.id} from parsed data")
            return candidate.id
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating candidate from parsed data: {str(e)}")
            raise
    
    async def get_candidate_by_id(
        self,
        candidate_id: str,
        include_relations: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get candidate by ID with all related data
        
        Args:
            candidate_id: Candidate ID
            include_relations: Whether to include education, experience, etc.
            
        Returns:
            Candidate data dictionary or None
        """
        try:
            query = select(Candidate).where(Candidate.id == candidate_id)
            
            result = await self.db.execute(query)
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                return None
            
            # Build response
            candidate_data = {
                "id": candidate.id,
                "uuid": candidate.uuid,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "linkedin_url": candidate.linkedin_url,
                "location": candidate.location,
                "source": candidate.source,
                "status": candidate.status,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None
            }
            
            if include_relations:
                # Get education
                edu_result = await self.db.execute(
                    select(Education).where(Education.candidate_id == candidate_id)
                )
                education_list = []
                for edu in edu_result.scalars().all():
                    edu_dict = {
                        "id": edu.id,
                        "degree": edu.degree,
                        "field": edu.field,
                        "institution": edu.institution,
                        "location": edu.location,
                        "start_date": edu.start_date,
                        "end_date": edu.end_date,
                        "gpa": edu.gpa,
                        "confidence_score": edu.confidence_score
                    }
                    education_list.append(edu_dict)
                candidate_data["education"] = education_list
                
                # Get experience
                exp_result = await self.db.execute(
                    select(WorkExperience).where(WorkExperience.candidate_id == candidate_id)
                )
                experience_list = []
                for exp in exp_result.scalars().all():
                    exp_dict = {
                        "id": exp.id,
                        "company": exp.company,
                        "title": exp.title,
                        "location": exp.location,
                        "start_date": exp.start_date,
                        "end_date": exp.end_date,
                        "is_current": exp.is_current,
                        "duration_months": exp.duration_months,
                        "description": exp.description,
                        "confidence_score": exp.confidence_score
                    }
                    experience_list.append(exp_dict)
                candidate_data["experience"] = experience_list
                
                # Get skills
                skills_result = await self.db.execute(
                    select(Skill, CandidateSkill)
                    .join(CandidateSkill, Skill.id == CandidateSkill.skill_id)
                    .where(CandidateSkill.candidate_id == candidate_id)
                )
                candidate_data["skills"] = [
                    {
                        "id": skill.id,
                        "name": skill.name,
                        "category": skill.category,
                        "proficiency": cs.proficiency,
                        "confidence_score": cs.confidence_score
                    }
                    for skill, cs in skills_result.all()
                ]
                
                # Get certifications
                cert_result = await self.db.execute(
                    select(Certification).where(Certification.candidate_id == candidate_id)
                )
                certifications_list = []
                for cert in cert_result.scalars().all():
                    cert_dict = {
                        "id": cert.id,
                        "name": cert.name,
                        "issuer": cert.issuer,
                        "issue_date": cert.issue_date,
                        "expiry_date": cert.expiry_date,
                        "credential_id": cert.credential_id,
                        "confidence_score": cert.confidence_score
                    }
                    certifications_list.append(cert_dict)
                candidate_data["certifications"] = certifications_list
            
            return candidate_data
            
        except Exception as e:
            logger.error(f"Error getting candidate {candidate_id}: {str(e)}")
            raise
    
    async def update_candidate(
        self,
        candidate_id: str,
        update_data: CandidateUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        Update candidate information
        
        Args:
            candidate_id: Candidate ID
            update_data: Update data
            
        Returns:
            Updated candidate data or None
        """
        try:
            result = await self.db.execute(
                select(Candidate).where(Candidate.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                return None
            
            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(candidate, field, value)
            
            await self.db.commit()
            await self.db.refresh(candidate)
            
            logger.info(f"Updated candidate {candidate_id}")
            return await self.get_candidate_by_id(candidate_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating candidate {candidate_id}: {str(e)}")
            raise
    
    async def search_candidates(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search and filter candidates with pagination
        
        Args:
            search: Search term (name, email, phone)
            status: Filter by status
            page: Page number
            limit: Items per page
            
        Returns:
            Paginated candidates list
        """
        try:
            # Build query
            query = select(Candidate)
            
            # Apply filters
            filters = []
            if search:
                search_term = f"%{search}%"
                filters.append(
                    or_(
                        Candidate.full_name.ilike(search_term),
                        Candidate.email.ilike(search_term),
                        Candidate.phone.ilike(search_term)
                    )
                )
            
            if status:
                filters.append(Candidate.status == status)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Get total count
            count_query = select(func.count()).select_from(Candidate)
            if filters:
                count_query = count_query.where(and_(*filters))
            
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit).order_by(Candidate.created_at.desc())
            
            result = await self.db.execute(query)
            candidates = result.scalars().all()
            
            # Build response
            candidate_list = []
            for candidate in candidates:
                # Get counts
                edu_count = await self.db.execute(
                    select(func.count()).select_from(Education).where(Education.candidate_id == candidate.id)
                )
                skills_count = await self.db.execute(
                    select(func.count()).select_from(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id)
                )
                
                # Calculate total experience
                exp_result = await self.db.execute(
                    select(func.sum(WorkExperience.duration_months))
                    .where(WorkExperience.candidate_id == candidate.id)
                )
                total_exp = exp_result.scalar() or 0
                
                candidate_list.append({
                    "id": candidate.id,
                    "uuid": candidate.uuid,
                    "full_name": candidate.full_name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "location": candidate.location,
                    "status": candidate.status,
                    "created_at": candidate.created_at,
                    "total_experience_months": total_exp,
                    "education_count": edu_count.scalar(),
                    "skills_count": skills_count.scalar()
                })
            
            return {
                "candidates": candidate_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching candidates: {str(e)}")
            raise
    
    async def merge_candidates(
        self,
        source_id: str,
        target_id: str,
        merged_by: str
    ) -> str:
        """
        Merge two candidate records
        
        Args:
            source_id: Source candidate ID (will be archived)
            target_id: Target candidate ID (will be kept)
            merged_by: User ID performing the merge
            
        Returns:
            Target candidate ID
        """
        try:
            # Get both candidates
            source_result = await self.db.execute(
                select(Candidate).where(Candidate.id == source_id)
            )
            source = source_result.scalar_one_or_none()
            
            target_result = await self.db.execute(
                select(Candidate).where(Candidate.id == target_id)
            )
            target = target_result.scalar_one_or_none()
            
            if not source or not target:
                raise ValueError("Source or target candidate not found")
            
            # Update all related records to point to target
            await self.db.execute(
                select(Education).where(Education.candidate_id == source_id)
            )
            await self.db.execute(
                Education.__table__.update()
                .where(Education.candidate_id == source_id)
                .values(candidate_id=target_id)
            )
            
            await self.db.execute(
                WorkExperience.__table__.update()
                .where(WorkExperience.candidate_id == source_id)
                .values(candidate_id=target_id)
            )
            
            await self.db.execute(
                CandidateSkill.__table__.update()
                .where(CandidateSkill.candidate_id == source_id)
                .values(candidate_id=target_id)
            )
            
            await self.db.execute(
                Certification.__table__.update()
                .where(Certification.candidate_id == source_id)
                .values(candidate_id=target_id)
            )
            
            await self.db.execute(
                Resume.__table__.update()
                .where(Resume.candidate_id == source_id)
                .values(candidate_id=target_id)
            )
            
            # Archive source candidate
            source.status = "archived"
            
            await self.db.commit()
            logger.info(f"Merged candidate {source_id} into {target_id}")
            return target_id
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error merging candidates: {str(e)}")
            raise
    
    async def delete_candidate(
        self,
        candidate_id: str,
        deleted_by: str
    ) -> bool:
        """
        Delete a candidate (soft delete by archiving)
        
        Args:
            candidate_id: Candidate ID
            deleted_by: User ID performing deletion
            
        Returns:
            True if successful
        """
        try:
            result = await self.db.execute(
                select(Candidate).where(Candidate.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                return False
            
            candidate.status = "archived"
            await self.db.commit()
            
            logger.info(f"Deleted (archived) candidate {candidate_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting candidate {candidate_id}: {str(e)}")
            raise
