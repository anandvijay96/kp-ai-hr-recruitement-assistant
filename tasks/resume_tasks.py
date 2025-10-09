import logging
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from core.celery_app import celery_app
from core.database import get_async_session
from models.db import Resume, Candidate, Education, WorkExperience, Skill, Certification
from services.document_processor import DocumentProcessor
from services.enhanced_resume_extractor import EnhancedResumeExtractor
from services.resume_analyzer import ResumeAuthenticityAnalyzer
from services.duplicate_detector import DuplicateDetector

logger = logging.getLogger(__name__)


def _parse_year_to_date(year_str):
    """Helper function to convert year string to date object"""
    if not year_str:
        return None
    try:
        year = int(year_str)
        return datetime(year, 1, 1).date()
    except:
        return None


@celery_app.task(bind=True, name='tasks.resume_tasks.process_resume')
def process_resume(self, resume_id: int):
    """
    Background task to process a resume:
    1. Extract text from document
    2. Extract structured data (name, email, etc.)
    3. Analyze authenticity
    4. Check for duplicates
    5. Create/update candidate record
    6. Update resume status
    
    Args:
        resume_id: ID of the resume to process
    """
    db: Session = SessionLocal()
    
    try:
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Starting resume processing'})
        
        # Get resume from database
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise ValueError(f"Resume with id {resume_id} not found")
        
        # Update status to processing
        resume.upload_status = 'processing'
        db.commit()
        
        logger.info(f"Processing resume {resume_id}: {resume.file_name}")
        
        # Step 1: Extract text (or use existing if already extracted)
        if resume.raw_text and len(resume.raw_text.strip()) >= 50:
            text = resume.raw_text
            logger.info(f"Using pre-extracted text ({len(text)} chars)")
        else:
            self.update_state(state='PROCESSING', meta={'status': 'Extracting text from document'})
            doc_processor = DocumentProcessor()
            text = doc_processor.extract_text(resume.file_path)
            resume.raw_text = text
            db.commit()
            
            if not text or len(text.strip()) < 50:
                raise ValueError("Could not extract meaningful text from document")
        
        # Step 2: Extract structured data (or use existing if already extracted)
        if resume.extracted_data and isinstance(resume.extracted_data, dict) and resume.extracted_data.get('email'):
            extracted_data = resume.extracted_data
            logger.info(f"Using pre-extracted data: email={extracted_data.get('email')}, name={extracted_data.get('name')}")
        else:
            self.update_state(state='PROCESSING', meta={'status': 'Extracting structured data'})
            data_extractor = EnhancedResumeExtractor()
            extracted_data = data_extractor.extract_all(text)
            resume.extracted_data = extracted_data
            db.commit()
        
        logger.info(f"Extracted data: email={extracted_data.get('email')}, "
                   f"name={extracted_data.get('name')}, "
                   f"skills_count={len(extracted_data.get('skills', []))}, "
                   f"education_count={len(extracted_data.get('education', []))}, "
                   f"experience_count={len(extracted_data.get('work_experience', []))}")
        
        # Step 3: Analyze authenticity
        self.update_state(state='PROCESSING', meta={'status': 'Analyzing authenticity'})
        analyzer = ResumeAuthenticityAnalyzer()
        auth_result = analyzer.analyze_authenticity(resume.file_path, text)
        resume.authenticity_score = int(auth_result.get('overall_score', 0))
        resume.authenticity_details = auth_result
        db.commit()
        
        # Step 4: Check for duplicate candidate
        self.update_state(state='PROCESSING', meta={'status': 'Checking for duplicates'})
        candidate = None
        
        if extracted_data.get('email'):
            # Check if candidate exists by email
            candidate = db.query(Candidate).filter(
                Candidate.email == extracted_data['email']
            ).first()
            
            if candidate:
                logger.info(f"Found existing candidate: {candidate.id} ({candidate.email})")
        
        # Step 5: Create or update candidate (Enhanced)
        if not candidate and extracted_data.get('email'):
            self.update_state(state='PROCESSING', meta={'status': 'Creating candidate profile'})
            
            candidate = Candidate(
                full_name=extracted_data.get('name') or 'Unknown',
                email=extracted_data['email'],
                phone_number=extracted_data.get('phone'),
                linkedin_url=extracted_data.get('linkedin_url'),
                github_url=extracted_data.get('github_url'),
                portfolio_url=extracted_data.get('portfolio_url'),
                location=extracted_data.get('location'),
                professional_summary=extracted_data.get('summary'),
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            logger.info(f"Created new candidate: {candidate.id} ({candidate.email})")
            
            # Add education records with enhanced fields
            for edu in extracted_data.get('education', []):
                try:
                    education = Education(
                        candidate_id=candidate.id,
                        degree=edu.get('degree'),
                        field_of_study=edu.get('field_of_study'),
                        institution=edu.get('institution'),
                        grade=edu.get('gpa'),
                        # Parse dates if available
                        start_date=_parse_year_to_date(edu.get('start_year')),
                        end_date=_parse_year_to_date(edu.get('graduation_year')),
                    )
                    db.add(education)
                except Exception as e:
                    logger.warning(f"Error adding education record: {e}")
            
            # Add work experience records with enhanced fields
            for exp in extracted_data.get('work_experience', []):
                try:
                    # Parse dates
                    from dateutil import parser as date_parser
                    start_date = None
                    end_date = None
                    is_current = False
                    
                    try:
                        if exp.get('start_date'):
                            start_date = date_parser.parse(exp['start_date'], fuzzy=True).date()
                    except:
                        pass
                    
                    try:
                        if exp.get('end_date'):
                            if 'present' in exp['end_date'].lower():
                                is_current = True
                                end_date = None
                            else:
                                end_date = date_parser.parse(exp['end_date'], fuzzy=True).date()
                    except:
                        pass
                    
                    # Join responsibilities into description
                    description = '\n'.join(exp.get('responsibilities', []))
                    
                    experience = WorkExperience(
                        candidate_id=candidate.id,
                        company=exp.get('company'),
                        job_title=exp.get('title'),
                        location=exp.get('location'),
                        start_date=start_date,
                        end_date=end_date,
                        is_current=is_current,
                        description=description if description else None,
                    )
                    db.add(experience)
                except Exception as e:
                    logger.warning(f"Error adding work experience record: {e}")
            
            # Add certifications
            for cert in extracted_data.get('certifications', []):
                try:
                    certification = Certification(
                        candidate_id=candidate.id,
                        name=cert.get('name'),
                        issue_year=cert.get('year'),
                    )
                    db.add(certification)
                except Exception as e:
                    logger.warning(f"Error adding certification: {e}")
            
            # Add skills
            for skill_name in extracted_data.get('skills', []):
                try:
                    # Normalize skill name (lowercase for storage)
                    skill_name_normalized = skill_name.lower()
                    
                    # Get or create skill
                    skill = db.query(Skill).filter(Skill.name == skill_name_normalized).first()
                    if not skill:
                        skill = Skill(name=skill_name_normalized)
                        db.add(skill)
                        db.flush()
                    
                    # Associate with candidate (avoid duplicates)
                    if skill not in candidate.skills:
                        candidate.skills.append(skill)
                except Exception as e:
                    logger.warning(f"Error adding skill '{skill_name}': {e}")
            
            db.commit()
            
            logger.info(f"Saved candidate data: {len(extracted_data.get('education', []))} education, "
                       f"{len(extracted_data.get('work_experience', []))} work experience, "
                       f"{len(extracted_data.get('certifications', []))} certifications, "
                       f"{len(extracted_data.get('skills', []))} skills")
        
        # Link resume to candidate
        if candidate:
            resume.candidate_id = candidate.id
        
        # Update resume status to completed
        resume.upload_status = 'completed'
        resume.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully processed resume {resume_id}")
        
        return {
            'status': 'success',
            'resume_id': resume_id,
            'candidate_id': candidate.id if candidate else None,
            'authenticity_score': resume.authenticity_score,
        }
        
    except Exception as e:
        logger.error(f"Error processing resume {resume_id}: {str(e)}", exc_info=True)
        
        # Update resume status to failed
        if resume:
            resume.upload_status = 'failed'
            resume.extracted_data = {'error': str(e)}
            db.commit()
        
        raise
    
    finally:
        db.close()


@celery_app.task(name='tasks.resume_tasks.cleanup_old_resumes')
def cleanup_old_resumes(days_old: int = 90):
    """
    Cleanup old resume files (optional maintenance task)
    
    Args:
        days_old: Delete resumes older than this many days
    """
    db: Session = SessionLocal()
    
    try:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_resumes = db.query(Resume).filter(
            Resume.uploaded_at < cutoff_date
        ).all()
        
        logger.info(f"Found {len(old_resumes)} resumes older than {days_old} days")
        
        # In production, you might want to archive instead of delete
        # For now, just log
        
        return {
            'status': 'success',
            'count': len(old_resumes),
        }
    
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        raise
    
    finally:
        db.close()
