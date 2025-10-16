"""
Resume Vetting API
Endpoints for scanning resumes without saving to database
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import hashlib
import uuid
import os
import re
import aiofiles

from core.database import get_db
from services.document_processor import DocumentProcessor
from services.resume_analyzer import ResumeAuthenticityAnalyzer
from services.jd_matcher import JDMatcher
from services.vetting_session import VettingSession
from services.google_search_verifier import GoogleSearchVerifier
from services.enhanced_resume_extractor import EnhancedResumeExtractor
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Google Search Verifier (if configured)
google_search_verifier = None
if settings.google_search_api_key and settings.google_search_engine_id:
    try:
        google_search_verifier = GoogleSearchVerifier(
            api_key=settings.google_search_api_key,
            search_engine_id=settings.google_search_engine_id
        )
    except Exception as e:
        logger.warning(f"Failed to initialize Google Search verifier: {e}")

# Initialize services
document_processor = DocumentProcessor()
resume_analyzer = ResumeAuthenticityAnalyzer(
    google_search_verifier=google_search_verifier,
    use_selenium=settings.use_selenium_verification if hasattr(settings, 'use_selenium_verification') else False
)
jd_matcher = JDMatcher()
vetting_session = VettingSession()
resume_data_extractor = EnhancedResumeExtractor()

@router.post("/scan")
async def scan_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    use_llm: bool = Form(False),
    llm_provider: str = Form("gemini")
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
        
        # Analyze document structure (CRITICAL: same as upload page)
        structure_info = document_processor.analyze_document_structure(temp_file_path)
        
        # Extract candidate information using LLM or traditional method
        candidate_name = None
        candidate_email = None
        candidate_phone = None
        extracted_data = None
        
        try:
            if use_llm:
                # Use LLM-based extraction
                logger.info(f"🤖 Using LLM extraction with provider: {llm_provider}")
                from services.llm_resume_extractor import create_llm_extractor
                from core.config import settings
                
                # Get API key from settings
                api_key = None
                if llm_provider == "gemini":
                    api_key = getattr(settings, 'gemini_api_key', None) or os.getenv('GEMINI_API_KEY')
                elif llm_provider == "openai":
                    api_key = getattr(settings, 'openai_api_key', None) or os.getenv('OPENAI_API_KEY')
                
                if not api_key:
                    logger.warning(f"⚠️ {llm_provider.upper()} API key not configured, falling back to traditional extraction")
                    use_llm = False
                else:
                    try:
                        llm_extractor = create_llm_extractor(provider=llm_provider, api_key=api_key)
                        extracted_data = llm_extractor.extract(extracted_text)
                        extracted_data = llm_extractor.validate_extraction(extracted_data)
                        
                        candidate_name = extracted_data.get('name')
                        candidate_email = extracted_data.get('email')
                        candidate_phone = extracted_data.get('phone')
                        logger.info(f"✅ LLM extraction successful: Name={candidate_name}, Email={candidate_email}, Phone={candidate_phone}")
                    except Exception as llm_error:
                        logger.error(f"❌ LLM extraction failed: {llm_error}, falling back to traditional")
                        use_llm = False
            
            if not use_llm:
                # Use traditional extraction
                logger.info(f"📋 Using traditional extraction (OCR + Regex)")
                extracted_data = resume_data_extractor.extract_all(extracted_text)
                if extracted_data:
                    candidate_name = extracted_data.get('name')
                    candidate_email = extracted_data.get('email')
                    candidate_phone = extracted_data.get('phone')
                    logger.info(f"📝 Extracted candidate data: Name={candidate_name}, Email={candidate_email}, Phone={candidate_phone}")
                else:
                    logger.warning(f"⚠️ No candidate data extracted from resume")
        except Exception as e:
            logger.warning(f"Failed to extract candidate data: {str(e)}")
        
        # Fallback: Extract name from filename if extraction failed
        if not candidate_name and file.filename:
            logger.info(f"🔄 Attempting to extract name from filename: {file.filename}")
            # Remove extension and common prefixes
            name_from_file = os.path.splitext(file.filename)[0]
            logger.info(f"   After removing extension: {name_from_file}")
            # Remove common prefixes like "Naukri_", "Resume_", etc.
            name_from_file = re.sub(r'^(Naukri|Resume|CV)_?', '', name_from_file, flags=re.IGNORECASE)
            logger.info(f"   After removing prefix: {name_from_file}")
            # Remove brackets and their contents (like [7y_4m])
            name_from_file = re.sub(r'\[.*?\]', '', name_from_file)
            logger.info(f"   After removing brackets: {name_from_file}")
            # Replace underscores and hyphens with spaces
            name_from_file = name_from_file.replace('_', ' ').replace('-', ' ').strip()
            # Split CamelCase names (e.g., "JohnDoe" -> "John Doe")
            name_from_file = re.sub(r'([a-z])([A-Z])', r'\1 \2', name_from_file)
            logger.info(f"   After cleanup: {name_from_file}")
            # Only use if it looks like a name (1-5 words, reasonable length)
            words = name_from_file.split()
            logger.info(f"   Words: {words}, Count: {len(words)}, Length: {len(name_from_file)}")
            # Accept if it has at least 1 word and reasonable length
            if 1 <= len(words) <= 5 and 3 <= len(name_from_file) < 50:
                candidate_name = name_from_file
                logger.info(f"✅ Using name from filename: {candidate_name}")
            else:
                logger.warning(f"⚠️ Filename-based name rejected: {len(words)} words (need 1-5), {len(name_from_file)} chars (need 3-50)")
        
        # Analyze authenticity (SAME as upload page with all parameters)
        authenticity_result = resume_analyzer.analyze_authenticity(
            text_content=extracted_text,
            structure_info=structure_info,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone
        )
        
        # JD matching if job description provided
        matching_result = None
        if job_description:
            matching_result = jd_matcher.match_resume_with_jd(extracted_text, job_description)
        
        # Generate comprehensive analysis with job hopping and education verification
        comprehensive_analysis = _generate_comprehensive_analysis(
            authenticity_result=authenticity_result,
            extracted_data=extracted_data
        )
        
        # Debug: Log work experience and job hopping analysis
        work_exp = extracted_data.get('work_experience', []) if extracted_data else []
        logger.info(f"📊 Work Experience Extracted: {len(work_exp)} entries")
        if work_exp:
            logger.info(f"📊 First entry: {work_exp[0]}")
        logger.info(f"📊 Job Hopping Analysis: {comprehensive_analysis.get('job_hopping', {})}")
        
        # Build scan result (INCLUDE extracted_data for later use)
        scan_result = {
            "filename": file.filename,
            "file_hash": file_hash,
            "file_size": len(content),
            "authenticity_score": authenticity_result,
            "comprehensive_analysis": comprehensive_analysis,
            "matching_score": matching_result,
            "extracted_text_length": len(extracted_text),
            "extracted_text": extracted_text,  # Store for database upload
            "extracted_data": extracted_data,   # Store candidate info for database upload
            "file_content": content.hex()  # Store file content as hex string for later retrieval
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


@router.post("/session/{session_id}/upload-approved")
async def upload_approved_to_database(session_id: str, db: Session = Depends(get_db)):
    """
    Upload approved resumes from vetting session to the database
    
    Args:
        session_id: Vetting session ID
        db: Database session
    
    Returns:
        Summary of uploaded resumes
    """
    from tasks.resume_tasks import process_resume
    from models.database import Resume, Candidate
    import shutil
    
    try:
        # Get approved resumes from session
        approved_resumes = vetting_session.get_approved_resumes(session_id)
        
        if not approved_resumes:
            raise HTTPException(status_code=404, detail="No approved resumes found in session")
        
        uploaded = []
        failed = []
        
        for resume_data in approved_resumes:
            try:
                file_hash = resume_data['file_hash']
                file_name = resume_data['file_name']
                
                # Check if already in database
                from sqlalchemy import select
                stmt = select(Resume).filter(Resume.file_hash == file_hash)
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    failed.append({
                        "file_name": file_name,
                        "reason": "Already in database",
                        "status": "duplicate"
                    })
                    continue
                
                # Copy file from temp to permanent storage
                temp_file_path = os.path.join("temp/vetting_files", f"{file_hash}_{file_name}")
                
                if not os.path.exists(temp_file_path):
                    failed.append({
                        "file_name": file_name,
                        "reason": "Temp file not found",
                        "status": "error"
                    })
                    continue
                
                permanent_file_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}_{file_name}")
                shutil.copy2(temp_file_path, permanent_file_path)
                
                # Get extracted data from scan result
                scan_result = resume_data.get('scan_result', {})
                extracted_text = scan_result.get('extracted_text', '')
                extracted_data = scan_result.get('extracted_data', {})
                
                # If extracted_data is None or empty, try to re-extract
                if not extracted_data or extracted_data is None:
                    logger.info(f"Re-extracting data for {file_name}")
                    try:
                        extracted_data = resume_data_extractor.extract_all(extracted_text)
                        if not extracted_data:
                            extracted_data = {}
                        else:
                            # Log what was extracted
                            logger.info(f"Extracted data keys: {list(extracted_data.keys())}")
                            logger.info(f"Education type: {type(extracted_data.get('education'))}, count: {len(extracted_data.get('education', []))}")
                            logger.info(f"Work experience type: {type(extracted_data.get('work_experience'))}, count: {len(extracted_data.get('work_experience', []))}")
                    except Exception as e:
                        logger.error(f"Failed to re-extract data: {e}")
                        extracted_data = {}
                
                # Extract candidate information from parsed data
                candidate_name = extracted_data.get('name') or extracted_data.get('full_name')
                candidate_email = extracted_data.get('email')
                candidate_phone = extracted_data.get('phone') or extracted_data.get('phone_number')
                
                # If still no name, try to extract from filename
                if not candidate_name:
                    # Try to get name from filename (remove extension and underscores)
                    candidate_name = os.path.splitext(file_name)[0].replace('_', ' ').replace('-', ' ').strip()
                    logger.info(f"Using filename as candidate name: {candidate_name}")
                
                # Validate candidate data before creating
                invalid_names = [
                    'PROFESSIONAL SUMMARY:', 'Profile', 'Unknown Candidate', 
                    'Key Responsibilities', 'CERTIFICATION', 'CONTACT', 'SKILLS', 
                    'EDUCATION', 'EXPERIENCE', 'SUMMARY', 'OBJECTIVE',
                    '', 'null', 'None'
                ]
                if not candidate_name or candidate_name.strip() in invalid_names:
                    logger.warning(f"Skipping resume with invalid name: {candidate_name}")
                    failed.append({
                        "file_name": resume_data.get('file_name'),
                        "reason": "Invalid or missing candidate name in resume",
                        "status": "error"
                    })
                    continue
                    
                # Generate a unique email if missing (using file hash)
                if not candidate_email or '@' not in candidate_email:
                    logger.warning(f"No valid email found for {candidate_name}, generating placeholder")
                    # Use file hash to create unique email
                    candidate_email = f"candidate_{file_hash[:12]}@placeholder.com"
                
                # Check if candidate already exists by email
                candidate = None
                if candidate_email:
                    from sqlalchemy import select
                    try:
                        stmt = select(Candidate).filter(Candidate.email == candidate_email)
                        result = await db.execute(stmt)
                        candidate = result.scalar_one_or_none()
                    except Exception as e:
                        # Handle case where professional_summary column might not exist in DB
                        if "professional_summary" in str(e):
                            logger.warning(f"Database schema mismatch detected. Please run migration script.")
                            # Query without professional_summary
                            stmt = select(
                                Candidate.id, Candidate.uuid, Candidate.full_name, 
                                Candidate.email, Candidate.phone, Candidate.linkedin_url,
                                Candidate.location, Candidate.source, Candidate.status,
                                Candidate.created_at, Candidate.updated_at, Candidate.created_by
                            ).filter(Candidate.email == candidate_email)
                            result = await db.execute(stmt)
                            row = result.fetchone()
                            if row:
                                # Reconstruct candidate object
                                candidate = Candidate(
                                    id=row.id, uuid=row.uuid, full_name=row.full_name,
                                    email=row.email, phone=row.phone, linkedin_url=row.linkedin_url,
                                    location=row.location, source=row.source, status=row.status,
                                    created_at=row.created_at, updated_at=row.updated_at,
                                    created_by=row.created_by
                                )
                        else:
                            raise
                
                # Create new candidate if doesn't exist
                if not candidate:
                    # Prepare candidate data
                    candidate_data = {
                        "id": str(uuid.uuid4()),
                        "full_name": candidate_name,
                        "email": candidate_email,
                        "phone": candidate_phone,
                        "linkedin_url": extracted_data.get('linkedin_url'),
                        "location": extracted_data.get('location'),
                        "source": "vetting",
                        "status": "new",
                        "created_by": None  # NULL for system-created candidates
                    }
                    
                    # Only add professional_summary if column exists
                    try:
                        candidate_data["professional_summary"] = extracted_data.get('summary')
                        candidate = Candidate(**candidate_data)
                    except Exception as e:
                        if "professional_summary" in str(e):
                            # Column doesn't exist, create without it
                            logger.warning("Creating candidate without professional_summary (column not in DB)")
                            del candidate_data["professional_summary"]
                            candidate = Candidate(**candidate_data)
                        else:
                            raise
                    
                    db.add(candidate)
                    await db.commit()
                    await db.refresh(candidate)
                    logger.info(f"Created new candidate: {candidate_name} (ID: {candidate.id})")
                    
                    # Store skills
                    skills_data = extracted_data.get('skills', [])
                    if skills_data:
                        from models.database import Skill, CandidateSkill
                        for skill_item in skills_data:
                            if not skill_item:
                                continue
                            
                            # Handle both string and dict formats
                            if isinstance(skill_item, dict):
                                skill_name = skill_item.get('name')
                                skill_category = skill_item.get('category', 'Technical')
                                skill_proficiency = skill_item.get('proficiency', 'intermediate')
                            else:
                                skill_name = str(skill_item)
                                skill_category = 'Technical'
                                skill_proficiency = 'intermediate'
                            
                            if not skill_name:
                                continue
                            
                            # Get or create skill
                            stmt = select(Skill).filter(Skill.name == skill_name)
                            result = await db.execute(stmt)
                            skill = result.scalar_one_or_none()
                            
                            if not skill:
                                skill = Skill(name=skill_name, category=skill_category)
                                db.add(skill)
                                await db.commit()
                                await db.refresh(skill)
                            
                            # Create candidate-skill relationship
                            candidate_skill = CandidateSkill(
                                candidate_id=candidate.id,
                                skill_id=skill.id,
                                proficiency=skill_proficiency
                            )
                            db.add(candidate_skill)
                        
                        await db.commit()
                    
                    # Store education
                    education_data = extracted_data.get('education', [])
                    if education_data and isinstance(education_data, list):
                        from models.database import Education
                        logger.info(f"Storing {len(education_data)} education records for {candidate_name}")
                        for edu in education_data:
                            if not isinstance(edu, dict):
                                logger.warning(f"Skipping invalid education entry: {type(edu)}")
                                continue
                            if not edu.get('degree') and not edu.get('institution'):
                                continue
                            education = Education(
                                candidate_id=candidate.id,
                                degree=edu.get('degree'),
                                field=edu.get('field_of_study') or edu.get('field'),
                                institution=edu.get('institution'),
                                start_date=edu.get('start_year') or edu.get('start_date'),
                                end_date=edu.get('graduation_year') or edu.get('end_year') or edu.get('end_date'),
                                gpa=edu.get('gpa')
                            )
                            db.add(education)
                        await db.commit()
                    else:
                        logger.warning(f"Education data is not a list: {type(education_data)}")
                    
                    # Store work experience
                    experience_data = extracted_data.get('work_experience', [])
                    if experience_data and isinstance(experience_data, list):
                        from models.database import WorkExperience
                        logger.info(f"Storing {len(experience_data)} work experience records for {candidate_name}")
                        for exp in experience_data:
                            if not isinstance(exp, dict):
                                logger.warning(f"Skipping invalid experience entry: {type(exp)}")
                                continue
                            if not exp.get('company') and not exp.get('title'):
                                logger.warning(f"Skipping experience with no company or title")
                                continue
                            
                            # Get description and limit length to avoid storing entire resume
                            description = exp.get('description', '') or exp.get('responsibilities', '')
                            if isinstance(description, list):
                                # If responsibilities is a list, join them
                                description = '\n• ' + '\n• '.join(str(item) for item in description[:5])  # Limit to first 5 items
                            elif isinstance(description, str):
                                # Check if it's suspiciously long (likely entire resume)
                                if len(description) > 2000:
                                    logger.warning(f"Description too long ({len(description)} chars), truncating")
                                    description = description[:500] + '...'
                                elif len(description) > 1000:
                                    description = description[:1000] + '...'
                            
                            logger.info(f"Adding work exp: {exp.get('title')} at {exp.get('company')} ({exp.get('start_date')} - {exp.get('end_date')})")
                            
                            work_exp = WorkExperience(
                                candidate_id=candidate.id,
                                company=exp.get('company'),
                                title=exp.get('title'),
                                location=exp.get('location'),
                                start_date=exp.get('start_date'),
                                end_date=exp.get('end_date'),
                                is_current=exp.get('is_current', False),
                                description=description
                            )
                            db.add(work_exp)
                        await db.commit()
                    elif isinstance(experience_data, str):
                        # If it's a string (entire resume text), don't store it
                        logger.error(f"Work experience is a string ({len(experience_data)} chars), not storing. Extraction failed!")
                    else:
                        logger.warning(f"Work experience data is not a list: {type(experience_data)}")
                    
                    # Store certifications
                    certifications_data = extracted_data.get('certifications', [])
                    if certifications_data:
                        from models.database import Certification
                        for cert in certifications_data:
                            if not cert.get('name'):
                                continue
                            certification = Certification(
                                candidate_id=candidate.id,
                                name=cert.get('name'),
                                issuer=cert.get('issuer'),
                                issue_date=cert.get('issue_date') or cert.get('year'),
                                expiry_date=cert.get('expiry_date'),
                                credential_id=cert.get('credential_id')
                            )
                            db.add(certification)
                        await db.commit()
                    
                    # Store projects
                    projects_data = extracted_data.get('projects', [])
                    if projects_data:
                        from models.database import Project
                        import json
                        logger.info(f"Storing {len(projects_data)} projects for {candidate_name}")
                        for proj in projects_data:
                            if not proj.get('name'):
                                continue
                            # Convert technologies list to JSON string
                            technologies = proj.get('technologies', [])
                            if isinstance(technologies, list):
                                technologies_json = json.dumps(technologies)
                            else:
                                technologies_json = None
                            
                            project = Project(
                                candidate_id=candidate.id,
                                name=proj.get('name'),
                                description=proj.get('description'),
                                technologies=technologies_json
                            )
                            db.add(project)
                        await db.commit()
                    
                    # Store languages
                    languages_data = extracted_data.get('languages', [])
                    if languages_data:
                        from models.database import Language
                        logger.info(f"Storing {len(languages_data)} languages for {candidate_name}")
                        for lang in languages_data:
                            if not lang.get('language'):
                                continue
                            language = Language(
                                candidate_id=candidate.id,
                                language=lang.get('language'),
                                proficiency=lang.get('proficiency')
                            )
                            db.add(language)
                        await db.commit()
                
                # Create resume record with extracted data
                # Get file info
                file_size = os.path.getsize(permanent_file_path)
                file_ext = os.path.splitext(file_name)[1].lower().replace('.', '')
                
                # Get assessment scores from scan result
                authenticity_score = scan_result.get('authenticity_score')
                matching_score = scan_result.get('matching_score')
                
                # Convert scores dict to integer if it's a dict with 'overall_score'
                if isinstance(authenticity_score, dict):
                    authenticity_score = int(authenticity_score.get('overall_score', 0))
                elif authenticity_score:
                    authenticity_score = int(authenticity_score)
                else:
                    authenticity_score = None
                
                if isinstance(matching_score, dict):
                    matching_score = int(matching_score.get('overall_score', 0))
                elif matching_score:
                    matching_score = int(matching_score)
                else:
                    matching_score = None
                
                # Convert parsed_data to JSON string for SQLite
                import json
                parsed_data_json = json.dumps(extracted_data) if extracted_data else None
                
                resume = Resume(
                    file_name=file_name,
                    original_file_name=file_name,
                    file_path=permanent_file_path,
                    file_size=file_size,
                    file_type=file_ext,
                    file_hash=file_hash,
                    mime_type=f"application/{file_ext}",
                    status="uploaded",
                    processing_status="completed",  # Mark as completed since we have all data
                    extracted_text=extracted_text,
                    parsed_data=parsed_data_json,  # Store as JSON string
                    authenticity_score=authenticity_score,
                    jd_match_score=matching_score,
                    uploaded_by=None,  # NULL for system uploads (no user context in vetting)
                    candidate_id=candidate.id,  # Link to candidate
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    candidate_phone=candidate_phone
                )
                db.add(resume)
                await db.commit()
                await db.refresh(resume)
                
                # Trigger background processing (optional - gracefully handle Redis connection errors)
                try:
                    process_resume.delay(resume.id)
                    logger.info(f"Triggered background processing for resume {resume.id}")
                except Exception as celery_error:
                    # Log but don't fail the upload if Celery/Redis is unavailable
                    logger.warning(f"Could not trigger background processing (Celery/Redis unavailable): {celery_error}")
                    logger.info("Resume uploaded successfully, but background processing skipped")
                
                uploaded.append({
                    "file_name": file_name,
                    "resume_id": resume.id,
                    "status": "processing"
                })
                
                logger.info(f"Uploaded approved resume: {file_name} (ID: {resume.id})")
                
            except Exception as e:
                logger.error(f"Error uploading {resume_data.get('file_name')}: {str(e)}")
                failed.append({
                    "file_name": resume_data.get('file_name'),
                    "reason": str(e),
                    "status": "error"
                })
                await db.rollback()
        
        return {
            "session_id": session_id,
            "total_approved": len(approved_resumes),
            "uploaded": len(uploaded),
            "failed": len(failed),
            "uploaded_resumes": uploaded,
            "failed_resumes": failed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading approved resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_comprehensive_analysis(authenticity_result: Dict[str, Any], extracted_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive analysis including job hopping and education verification
    
    Args:
        authenticity_result: Result from resume_analyzer.analyze_authenticity()
        extracted_data: Extracted resume data (from LLM or traditional extraction)
    
    Returns:
        Comprehensive analysis with final score, job hopping, education verification
    """
    try:
        base_score = authenticity_result.get('overall_score', 0)
        
        # Job Hopping Analysis
        job_hopping = _analyze_job_hopping(extracted_data)
        job_hop_impact = job_hopping.get('score_impact', 0)
        
        # Education Verification
        education_verification = _analyze_education(extracted_data)
        
        # Calculate final score
        final_score = base_score + job_hop_impact
        final_score = max(0, min(100, final_score))  # Clamp between 0-100
        
        # Determine recommendation
        if final_score >= 75:
            recommendation = 'qualified'
            badge = 'success'
        elif final_score >= 60:
            recommendation = 'review'
            badge = 'warning'
        else:
            recommendation = 'reject'
            badge = 'danger'
        
        return {
            'base_authenticity_score': base_score,
            'job_hopping': job_hopping,
            'job_hopping_impact': job_hop_impact,
            'education_verification': education_verification,
            'final_score': final_score,
            'recommendation': recommendation,
            'badge': badge
        }
        
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {e}")
        # Return safe defaults
        return {
            'base_authenticity_score': authenticity_result.get('overall_score', 0),
            'job_hopping': {'risk_level': 'none', 'score_impact': 0},
            'job_hopping_impact': 0,
            'education_verification': {'discrepancy_count': 0},
            'final_score': authenticity_result.get('overall_score', 0),
            'recommendation': 'review',
            'badge': 'warning'
        }


def _analyze_job_hopping(extracted_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze job hopping patterns with detailed breakdown"""
    try:
        if not extracted_data or 'work_experience' not in extracted_data:
            return {
                'risk_level': 'unknown',
                'score_impact': 0,
                'short_tenures': 0,
                'total_jobs': 0,
                'pattern': 'Unknown - no work experience data extracted',
                'average_tenure_months': 0,
                'career_level': 'unknown',
                'recommendation': 'Unable to analyze - work experience data not extracted. Manual review required.'
            }
        
        work_experience = extracted_data.get('work_experience', [])
        if not work_experience:
            return {
                'risk_level': 'unknown',
                'score_impact': 0,
                'short_tenures': 0,
                'total_jobs': 0,
                'pattern': 'Unknown - no work experience data extracted',
                'average_tenure_months': 0,
                'career_level': 'unknown',
                'recommendation': 'Unable to analyze - work experience data not extracted. Manual review required.'
            }
        
        # Group jobs by company to detect actual job changes (not internal promotions)
        company_tenures = {}
        for exp in work_experience:
            company = exp.get('company', 'Unknown Company').strip().lower()
            duration = exp.get('duration_months')
            
            # Handle None values safely
            if duration is None or not isinstance(duration, (int, float)):
                duration = 0
            else:
                duration = int(duration)
            
            # Aggregate duration by company (handles internal promotions)
            if company in company_tenures:
                company_tenures[company]['total_duration'] += duration
                company_tenures[company]['roles'].append({
                    'title': exp.get('title', 'Unknown Position'),
                    'duration': duration
                })
            else:
                company_tenures[company] = {
                    'company_name': exp.get('company', 'Unknown Company'),
                    'total_duration': duration,
                    'roles': [{
                        'title': exp.get('title', 'Unknown Position'),
                        'duration': duration
                    }]
                }
        
        # Analyze company-level job hopping (not role changes within same company)
        short_stints = []
        total_companies = len(company_tenures)
        total_months = sum(c['total_duration'] for c in company_tenures.values())
        
        # Identify current company (most recent with longest tenure or first in list)
        current_company = None
        if work_experience:
            # Assume first entry is most recent (LLM usually returns in reverse chronological order)
            most_recent = work_experience[0]
            current_company_name = most_recent.get('company', 'Unknown Company')
            current_company_key = current_company_name.strip().lower()
            
            if current_company_key in company_tenures:
                company_info = company_tenures[current_company_key]
                current_company = {
                    'company': current_company_name,
                    'total_duration': company_info['total_duration'],
                    'roles': [r['title'] for r in company_info['roles']],
                    'current_role': most_recent.get('title', 'Unknown Position')
                }
        
        for company_data in company_tenures.values():
            total_duration = company_data['total_duration']
            
            if total_duration > 0 and total_duration < 12:  # Short tenure at company level
                # Show all roles at this company
                roles_display = ', '.join([r['title'] for r in company_data['roles']])
                short_stints.append({
                    'title': roles_display,
                    'company': company_data['company_name'],
                    'duration_months': total_duration,
                    'duration_display': f"{total_duration} month{'s' if total_duration != 1 else ''}"
                })
        
        short_tenure_count = len(short_stints)
        avg_tenure_months = total_months / total_companies if total_companies > 0 else 0
        
        # Determine career level based on total experience
        total_years = total_months / 12
        if total_years < 2:
            career_level = 'junior'
        elif total_years < 5:
            career_level = 'mid-level'
        else:
            career_level = 'senior'
        
        # Calculate risk based on career level
        if short_tenure_count == 0:
            risk_level = 'none'
            score_impact = 0
        elif short_tenure_count == 1:
            risk_level = 'low'
            score_impact = -3
        elif short_tenure_count == 2:
            risk_level = 'medium'
            score_impact = -7
        else:  # 3+ short tenures
            risk_level = 'high'
            score_impact = -12
        
        # Generate recommendation
        if risk_level == 'high':
            recommendation = f"High concern. Pattern of frequent job changes detected. Strongly recommend discussing career stability and long-term commitment."
        elif risk_level == 'medium':
            recommendation = f"Moderate concern. {short_tenure_count} short stints detected. Discuss reasons for job changes during interview."
        elif risk_level == 'low':
            recommendation = f"Low concern. One short stint may be acceptable. Verify reason during interview."
        else:
            recommendation = "No job hopping concerns detected. Stable career progression."
        
        return {
            'risk_level': risk_level,
            'score_impact': score_impact,
            'short_tenures': short_tenure_count,
            'total_jobs': total_companies,  # Total unique companies, not roles
            'pattern': f"frequent job changes" if short_tenure_count > 2 else f"{short_tenure_count} of {total_companies} companies < 12 months",
            'recent_short_stints': short_stints[:3],  # Show up to 3 most recent
            'current_company': current_company,  # Current employer details
            'average_tenure_months': round(avg_tenure_months, 1),
            'career_level': career_level,
            'recommendation': recommendation
        }
        
    except Exception as e:
        logger.error(f"Job hopping analysis error: {e}")
        return {
            'risk_level': 'unknown',
            'score_impact': 0,
            'short_tenures': 0,
            'total_jobs': 0,
            'pattern': 'Unknown - analysis error',
            'average_tenure_months': 0,
            'career_level': 'unknown',
            'recommendation': 'Unable to analyze - error occurred. Manual review required.'
        }


def _analyze_education(extracted_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze education verification"""
    try:
        if not extracted_data or 'education' not in extracted_data:
            return {'discrepancy_count': 0, 'requires_manual_review': False}
        
        education = extracted_data.get('education', [])
        if not education:
            return {'discrepancy_count': 0, 'requires_manual_review': False, 'recommendation': 'No education data found'}
        
        # For now, just return basic info
        # In future, can add cross-verification with uploaded documents
        return {
            'discrepancy_count': 0,
            'requires_manual_review': False,
            'total_entries': len(education),
            'recommendation': f'Found {len(education)} education entries - manual verification recommended'
        }
        
    except Exception as e:
        logger.error(f"Education analysis error: {e}")
        return {'discrepancy_count': 0, 'requires_manual_review': False}


@router.get("/session/{session_id}/resume/{file_hash}")
async def get_resume_file(session_id: str, file_hash: str):
    """
    Get the original resume file for viewing
    
    Args:
        session_id: Vetting session ID
        file_hash: File hash of the resume
    
    Returns:
        The original file content with appropriate content type
    """
    try:
        # Get session data
        session_data = vetting_session.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Find the resume in scanned resumes
        scanned_resumes = session_data.get('scanned_resumes', {})
        resume_data = scanned_resumes.get(file_hash)
        
        if not resume_data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Get file content from scan result
        scan_result = resume_data.get('scan_result', {})
        file_content_hex = scan_result.get('file_content')
        
        if not file_content_hex:
            raise HTTPException(status_code=404, detail="File content not available")
        
        # Convert hex string back to bytes
        file_content = bytes.fromhex(file_content_hex)
        
        # Determine content type based on filename
        filename = scan_result.get('filename', '')
        if filename.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif filename.lower().endswith(('.doc', '.docx')):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            content_type = 'application/octet-stream'
        
        # Return file with appropriate headers
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Cache-Control': 'no-cache'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resume file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
