#!/usr/bin/env python3
"""
Fix old candidates with 'Unknown' names by re-extracting from their resumes
"""
import logging
from core.database import SessionLocal
from models.db import Candidate, Resume
from services.enhanced_resume_extractor import EnhancedResumeExtractor
from services.document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_old_candidates():
    """Re-extract data for candidates with 'Unknown' names"""
    db = SessionLocal()
    extractor = EnhancedResumeExtractor()
    doc_processor = DocumentProcessor()
    
    try:
        # Find all candidates with 'Unknown' name
        unknown_candidates = db.query(Candidate).filter(
            Candidate.full_name == 'Unknown'
        ).all()
        
        logger.info(f"Found {len(unknown_candidates)} candidates with 'Unknown' name")
        
        for candidate in unknown_candidates:
            logger.info(f"\nProcessing Candidate ID {candidate.id} ({candidate.email})")
            
            # Get their resumes
            resumes = db.query(Resume).filter(Resume.candidate_id == candidate.id).all()
            
            if not resumes:
                logger.warning(f"  No resumes found for candidate {candidate.id}")
                continue
            
            # Use the first resume
            resume = resumes[0]
            logger.info(f"  Using resume: {resume.file_name}")
            
            # Extract text if not already done
            if not resume.raw_text or len(resume.raw_text.strip()) < 50:
                logger.info(f"  Extracting text from {resume.file_path}")
                text = doc_processor.extract_text(resume.file_path)
                resume.raw_text = text
                db.commit()
            else:
                text = resume.raw_text
                logger.info(f"  Using existing text ({len(text)} chars)")
            
            # Extract structured data
            logger.info(f"  Extracting structured data...")
            extracted_data = extractor.extract_all(text)
            
            # Update resume
            resume.extracted_data = extracted_data
            db.commit()
            
            # Try to get name from extracted_data or parse from text
            name = extracted_data.get('name')
            
            # Fallback: Try to extract name from first few lines
            if not name or name == 'Unknown':
                import re
                lines = text.strip().split('\n')[:10]  # First 10 lines
                for line in lines:
                    line = line.strip()
                    # Look for name pattern (2-4 words, title case, not too long)
                    if len(line) > 5 and len(line) < 50:
                        words = line.split()
                        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                            # Avoid common headers
                            if not any(keyword in line.lower() for keyword in ['email', 'phone', 'contact', 'linkedin', 'resume', 'cv', 'developer', 'engineer', 'manager']):
                                name = line
                                logger.info(f"  📝 Extracted name from text: {name}")
                                break
            
            # Update candidate
            if name and name != 'Unknown':
                logger.info(f"  ✅ Found name: {name}")
                candidate.full_name = name
                
                # Update other fields if available
                if extracted_data.get('linkedin_url'):
                    candidate.linkedin_url = extracted_data['linkedin_url']
                if extracted_data.get('github_url'):
                    candidate.github_url = extracted_data['github_url']
                if extracted_data.get('location'):
                    candidate.location = extracted_data['location']
                if extracted_data.get('summary'):
                    candidate.professional_summary = extracted_data['summary']
                
                db.commit()
                logger.info(f"  ✅ Updated candidate {candidate.id} -> {name}")
            else:
                logger.warning(f"  ⚠️ Could not extract name from resume")
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ Fix completed!")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_old_candidates()
