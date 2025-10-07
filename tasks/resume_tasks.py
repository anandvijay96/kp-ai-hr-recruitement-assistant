import logging
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from core.celery_app import celery_app
from core.database import SessionLocal
from models.db import Resume, Candidate, Education, WorkExperience, Skill
from services.document_processor import DocumentProcessor
from services.resume_data_extractor import ResumeDataExtractor
from services.resume_analyzer import ResumeAuthenticityAnalyzer

logger = logging.getLogger(__name__)

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
        
        # Step 1: Extract text
        self.update_state(state='PROCESSING', meta={'status': 'Extracting text from document'})
        doc_processor = DocumentProcessor()
        text = doc_processor.extract_text(resume.file_path)
        resume.raw_text = text
        db.commit()
        
        if not text or len(text.strip()) < 50:
            raise ValueError("Could not extract meaningful text from document")
        
        # Step 2: Extract structured data
        self.update_state(state='PROCESSING', meta={'status': 'Extracting structured data'})
        data_extractor = ResumeDataExtractor()
        extracted_data = data_extractor.extract_all(text)
        resume.extracted_data = extracted_data
        db.commit()
        
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
        
        # Step 5: Create or update candidate
        if not candidate and extracted_data.get('email'):
            self.update_state(state='PROCESSING', meta={'status': 'Creating candidate profile'})
            
            candidate = Candidate(
                full_name=extracted_data.get('name') or 'Unknown',
                email=extracted_data['email'],
                phone_number=extracted_data.get('phone'),
                linkedin_url=extracted_data.get('linkedin_url'),
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            logger.info(f"Created new candidate: {candidate.id} ({candidate.email})")
            
            # Add education records
            for edu in extracted_data.get('education', []):
                education = Education(
                    candidate_id=candidate.id,
                    degree=edu.get('degree'),
                    institution=edu.get('institution'),
                )
                db.add(education)
            
            # Add work experience records
            for exp in extracted_data.get('work_experience', []):
                experience = WorkExperience(
                    candidate_id=candidate.id,
                    company=exp.get('company'),
                    job_title=exp.get('title'),
                )
                db.add(experience)
            
            # Add skills
            for skill_name in extracted_data.get('skills', []):
                # Get or create skill
                skill = db.query(Skill).filter(Skill.name == skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.add(skill)
                    db.flush()
                
                # Associate with candidate
                if skill not in candidate.skills:
                    candidate.skills.append(skill)
            
            db.commit()
        
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
