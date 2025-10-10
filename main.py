from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import uuid
from typing import List
import logging
import aiofiles

from core.config import settings
from core.auth import require_auth, get_current_user
from core.cache import SimpleCache
from models.schemas import ResumeAnalysis, JobDescription, AuthenticityScore, MatchingScore
from services.document_processor import DocumentProcessor
from services.resume_analyzer import ResumeAuthenticityAnalyzer
from services.jd_matcher import JDMatcher
from services.result_storage import ResultStorage
from services.google_search_verifier import GoogleSearchVerifier
from services.resume_data_extractor import ResumeDataExtractor
from api.v1 import resumes as resumes_v1
from api.v1 import candidates as candidates_v1
from api.v1 import auth as auth_v1
from api.v1 import simple_auth
try:
    from api.v1 import vetting as vetting_v1
    VETTING_ENABLED = True
except ImportError:
    VETTING_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.warning("Vetting module not available")

# Import new API modules from feature/job-creation branch
try:
    from api import auth as api_auth
    from api import jobs as api_jobs
    from api import jobs_management as api_jobs_management
    from api import users as api_users
    from api import resumes as api_resumes
    from api import candidates as api_candidates
    API_V2_ENABLED = True
except ImportError as e:
    API_V2_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.warning(f"New API modules not available: {e}")

from core.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Resume authenticity scanning and JD matching system with OAuth",
    version="2.0.0"
)

# Add session middleware for authentication
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key if hasattr(settings, 'secret_key') else "your-secret-key-change-in-production-please",
    session_cookie="hr_session",
    max_age=86400  # 24 hours
)

# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    """Initialize database tables on startup"""
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

# Mount static files (only if directory exists)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize services
document_processor = DocumentProcessor()
resume_data_extractor = ResumeDataExtractor()

# Initialize Google Search Verifier (if API credentials are configured)
google_search_verifier = None
if settings.google_search_api_key and settings.google_search_engine_id:
    google_search_verifier = GoogleSearchVerifier(
        api_key=settings.google_search_api_key,
        search_engine_id=settings.google_search_engine_id
    )
    logger.info("Google Search verification enabled for LinkedIn profile checks")
else:
    logger.info("Google Search API not configured - LinkedIn verification will be limited to resume content only")

# Initialize resume analyzer with optional Google verification and Selenium
resume_analyzer = ResumeAuthenticityAnalyzer(
    google_search_verifier=google_search_verifier,
    use_selenium=settings.use_selenium_verification
)
jd_matcher = JDMatcher()
result_storage = ResultStorage(settings.results_dir)
analysis_cache = SimpleCache(ttl_minutes=30)  # Cache results for 30 minutes

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.results_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)

# Include API v1 routers
app.include_router(resumes_v1.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(candidates_v1.router, prefix="/api/v1/candidates", tags=["candidates"])
app.include_router(simple_auth.router, prefix="/api/auth", tags=["auth"])
if VETTING_ENABLED:
    app.include_router(vetting_v1.router, prefix="/api/v1/vetting", tags=["vetting"])

# Include new API routers (job management, user management features)
if API_V2_ENABLED:
    app.include_router(api_auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(api_jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(api_jobs_management.router, prefix="/api/jobs-management", tags=["jobs-management"])
    app.include_router(api_users.router, prefix="/api/users", tags=["users"])
    app.include_router(api_resumes.router, prefix="/api/resumes", tags=["resumes"])
    app.include_router(api_candidates.router, prefix="/api/candidates", tags=["candidates"])

@app.get("/", response_class=HTMLResponse)
@require_auth
async def home(request: Request):
    """Main dashboard - requires authentication"""
    user = await get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Resume upload form"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/vet-resumes", response_class=HTMLResponse)
@require_auth
async def vet_resumes_page(request: Request):
    """Resume vetting page - requires authentication"""
    user = await get_current_user(request)
    return templates.TemplateResponse("vet_resumes.html", {"request": request, "user": user})

@app.get("/candidates")
@require_auth
async def candidates_list_page(request: Request):
    """Candidates list/search page - requires authentication"""
    user = await get_current_user(request)
    return templates.TemplateResponse("candidate_search.html", {"request": request, "user": user})

@app.get("/search")
def search_page(request: Request):
    """Candidate search and filtering page."""
    return templates.TemplateResponse("candidate_search.html", {"request": request})

@app.get("/candidates/{candidate_id}")
@require_auth
async def candidate_detail_page(request: Request, candidate_id: str):
    """Candidate detail page - requires authentication"""
    user = await get_current_user(request)
    return templates.TemplateResponse("candidate_detail.html", {
        "request": request,
        "candidate_id": candidate_id,
        "user": user
    })

@app.get("/resumes/{resume_id}/preview")
def resume_preview_page(resume_id: int, request: Request):
    """Resume preview page."""
    return templates.TemplateResponse("resume_preview.html", {"request": request})

# New routes for job and user management features
@app.get("/jobs", response_class=HTMLResponse)
@require_auth
async def jobs_list_page(request: Request):
    """Jobs list page - requires authentication"""
    user = await get_current_user(request)
    return templates.TemplateResponse("jobs/job_list.html", {"request": request, "user": user})

@app.get("/jobs/create", response_class=HTMLResponse)
async def job_create_page(request: Request):
    """Job creation page."""
    return templates.TemplateResponse("jobs/job_create.html", {"request": request})

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail_page(job_id: str, request: Request):
    """Job detail page."""
    return templates.TemplateResponse("jobs/job_detail.html", {"request": request, "job_id": job_id})

@app.get("/jobs-management", response_class=HTMLResponse)
@require_auth
async def jobs_management_dashboard(request: Request):
    """Jobs management dashboard - requires authentication"""
    user = await get_current_user(request)
    return templates.TemplateResponse("jobs_management/dashboard.html", {"request": request, "user": user})

@app.get("/users", response_class=HTMLResponse)
@require_auth
async def users_dashboard(request: Request):
    """User management dashboard - requires authentication"""
    user = await get_current_user(request)
    return templates.TemplateResponse("users/dashboard.html", {"request": request, "user": user})

@app.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page."""
    return templates.TemplateResponse("auth/register.html", {"request": request})

# Shortcut routes (redirect to /auth/* paths)
@app.get("/login", response_class=HTMLResponse)
async def login_shortcut(request: Request):
    """Shortcut for login page - simple MVP login."""
    return templates.TemplateResponse("auth/simple_login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_shortcut(request: Request):
    """Shortcut for registration page."""
    return templates.TemplateResponse("auth/register.html", {"request": request})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page."""
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request})

@app.post("/api/scan-resume")
async def scan_resume(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(None)
):
    """Scan resume for authenticity and match with JD"""
    try:
        # Validate file exists and has content
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file provided. Please select a file to upload."
            )

        # Validate file extension
        if not file.filename.lower().endswith(tuple(settings.allowed_extensions)):
            raise HTTPException(
                status_code=400,
                detail=f"File type '{os.path.splitext(file.filename)[1]}' not allowed. Supported formats: {', '.join(settings.allowed_extensions)}"
            )

        # Read file content and validate size
        content = await file.read()
        file_size = len(content)
        
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty. Please upload a valid document."
            )
        
        if file_size > settings.max_file_size:
            max_size_mb = settings.max_file_size / (1024 * 1024)
            actual_size_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File size ({actual_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb:.0f}MB)."
            )

        # Check cache for existing analysis
        jd_text = job_description if job_description and isinstance(job_description, str) else None
        cached_result = analysis_cache.get(content, jd_text)
        if cached_result:
            logger.info(f"Returning cached result for {file.filename}")
            return ResumeAnalysis(**cached_result)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.upload_dir, safe_filename)

        # Save uploaded file
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save uploaded file. Please try again."
            )

        # Process document
        try:
            text_content = document_processor.extract_text(file_path)
            
            # Check if text extraction was successful
            if not text_content or "Error processing document" in text_content:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to extract text from document. The file may be corrupted or password-protected."
                )
            
            if "not available" in text_content.lower():
                raise HTTPException(
                    status_code=500,
                    detail="Document processing libraries not available. Please contact support."
                )
                
            structure_info = document_processor.analyze_document_structure(file_path)
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )

        # Extract candidate information for Google verification
        try:
            extracted_data = resume_data_extractor.extract_all(text_content)
            # Safety check: ensure extracted_data is not None
            if extracted_data is None:
                logger.warning("Extractor returned None, using empty data")
                extracted_data = {}
            
            candidate_name = extracted_data.get('name')
            candidate_email = extracted_data.get('email')
            candidate_phone = extracted_data.get('phone')
        except Exception as e:
            logger.warning(f"Failed to extract candidate data: {str(e)}")
            candidate_name = None
            candidate_email = None
            candidate_phone = None

        # Analyze resume authenticity using real criteria (with Google verification if configured)
        try:
            authenticity_analysis = resume_analyzer.analyze_authenticity(
                text_content, 
                structure_info,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone
            )
            
            # Safety check
            if authenticity_analysis is None:
                logger.error("analyze_authenticity returned None!")
                raise ValueError("Authenticity analysis returned None")
                
        except Exception as e:
            import traceback
            logger.error(f"Error in authenticity analysis: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        authenticity_score = AuthenticityScore(
            overall_score=authenticity_analysis.get('overall_score', 0),
            font_consistency=authenticity_analysis.get('font_consistency', 0),
            grammar_score=authenticity_analysis.get('grammar_score', 0),
            formatting_score=authenticity_analysis.get('formatting_score', 0),
            visual_consistency=authenticity_analysis.get('visual_consistency', 0),
            linkedin_profile_score=authenticity_analysis.get('linkedin_profile_score', 0),
            capitalization_score=authenticity_analysis.get('capitalization_score', 0),
            details=authenticity_analysis.get('details', []),
            flags=authenticity_analysis.get('flags', []),
            diagnostics=authenticity_analysis.get('diagnostics', {})
        )

        # Implement JD matching if provided
        matching_score = None
        if job_description and isinstance(job_description, str) and job_description.strip():
            match_result = jd_matcher.match_resume_with_jd(text_content, job_description)
            matching_score = MatchingScore(
                overall_match=match_result['overall_match'],
                skills_match=match_result['skills_match'],
                experience_match=match_result['experience_match'],
                education_match=match_result['education_match'],
                matched_skills=match_result['matched_skills'],
                missing_skills=match_result['missing_skills'],
                details=match_result['details']
            )

        # Create analysis result
        analysis = ResumeAnalysis(
            id=file_id,
            filename=file.filename,
            file_size=len(content),
            authenticity_score=authenticity_score,
            matching_score=matching_score
        )

        # Save result to storage
        try:
            result_storage.save_result(analysis.dict())
        except Exception as e:
            logger.warning(f"Failed to save result to storage: {str(e)}")
            # Don't fail the request if storage fails

        # Cache the result for future requests
        try:
            analysis_cache.set(content, analysis.dict(), jd_text)
        except Exception as e:
            logger.warning(f"Failed to cache result: {str(e)}")

        return analysis

    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your resume. Please try again or contact support."
        )
    finally:
        # Clean up uploaded file if processing failed
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                # Keep successful uploads, only delete on error
                if 'analysis' not in locals():
                    os.remove(file_path)
                    logger.info(f"Cleaned up failed upload: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up file {file_path}: {str(cleanup_error)}")

@app.post("/api/batch-scan")
async def batch_scan_resumes(
    request: Request,
    files: List[UploadFile] = File(...),
    job_description: str = Form(None)
):
    """Batch scan multiple resumes with async processing and optional JD matching"""
    try:
        # Validate batch upload
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="No files provided. Please select at least one file to upload."
            )
        
        # Limit batch size
        max_batch_size = 10
        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Maximum {max_batch_size} files allowed per batch."
            )

        results = []
        errors = []

        # Process files concurrently for better performance
        import asyncio
        
        async def process_single_file(file: UploadFile):
            try:
                result = await scan_resume(request, file, job_description=job_description)
                return {"success": True, "result": result}
            except HTTPException as e:
                return {"success": False, "error": f"{file.filename}: {e.detail}"}
            except Exception as e:
                return {"success": False, "error": f"{file.filename}: Unexpected error - {str(e)}"}

        # Process all files concurrently
        tasks = [process_single_file(file) for file in files]
        processed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful results from errors
        for result in processed_results:
            if isinstance(result, Exception):
                errors.append(f"Processing error: {str(result)}")
            elif result.get("success"):
                results.append(result["result"])
            else:
                errors.append(result.get("error", "Unknown error"))

        return {
            "total_processed": len(files),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during batch processing. Please try again."
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0"
    }

@app.get("/api/results")
async def get_all_results(limit: int = 50):
    """Get all stored analysis results"""
    try:
        results = result_storage.get_all_results(limit=limit)
        return {
            "total": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve results")

@app.get("/api/results/{result_id}")
async def get_result_by_id(result_id: str):
    """Get a specific analysis result by ID"""
    try:
        result = result_storage.get_result_by_id(result_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving result: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve result")

@app.delete("/api/results/{result_id}")
async def delete_result(result_id: str):
    """Delete a specific analysis result"""
    try:
        success = result_storage.delete_result(result_id)
        if not success:
            raise HTTPException(status_code=404, detail="Result not found")
        return {"message": "Result deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting result: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete result")

@app.get("/api/statistics")
async def get_statistics():
    """Get statistics about stored results and cache"""
    try:
        storage_stats = result_storage.get_statistics()
        cache_stats = analysis_cache.get_stats()
        
        return {
            **storage_stats,
            'cache': cache_stats
        }
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate statistics")

@app.get("/api/export/csv")
async def export_results_csv():
    """Export results to CSV file"""
    try:
        import tempfile
        from fastapi.responses import FileResponse
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_path = temp_file.name
        temp_file.close()
        
        # Export to CSV
        success = result_storage.export_to_csv(temp_path)
        if not success:
            raise HTTPException(status_code=404, detail="No results to export")
        
        return FileResponse(
            temp_path,
            media_type='text/csv',
            filename=f'resume_analysis_results_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export results")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
