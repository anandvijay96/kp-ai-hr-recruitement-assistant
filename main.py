from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uuid
from typing import List
import logging
import aiofiles

from core.config import settings
from core.cache import SimpleCache
from core.database import init_db, close_db
from core.redis_client import redis_client
from models.schemas import ResumeAnalysis, JobDescription, AuthenticityScore, MatchingScore
from services.document_processor import DocumentProcessor
from services.resume_analyzer import ResumeAuthenticityAnalyzer
from services.jd_matcher import JDMatcher
from services.result_storage import ResultStorage
from api import auth, resumes, candidates, jobs, jobs_management, users

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="AI-powered HR recruitment system with resume authenticity scanning and JD matching",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(candidates.router)
app.include_router(jobs.router)
app.include_router(jobs_management.router)  # NEW: Jobs Management feature
app.include_router(users.router)  # NEW: User Management feature

# Mount static files (only if directory exists)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize services
document_processor = DocumentProcessor()
resume_analyzer = ResumeAuthenticityAnalyzer()
jd_matcher = JDMatcher()
result_storage = ResultStorage(settings.results_dir)
analysis_cache = SimpleCache(ttl_minutes=30)  # Cache results for 30 minutes

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.results_dir, exist_ok=True)
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database
        await init_db()
        logger.info("✓ Database initialized")
        
        # Auto-apply migration if needed
        import sqlite3
        
        db_path = "hr_recruitment.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if users table exists first
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                logger.warning("⚠️  Users table doesn't exist - creating...")
            
            # Check if status column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'status' not in columns:
                logger.warning("⚠️  Status column missing - Auto-applying migration...")
                
                # Read and apply migration
                sql_file = "migrations/010_create_user_management_tables.sql"
                if os.path.exists(sql_file):
                    with open(sql_file, 'r') as f:
                        sql_script = f.read()
                    
                    statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')]
                    
                    applied_count = 0
                    for statement in statements:
                        try:
                            cursor.execute(statement)
                            applied_count += 1
                        except sqlite3.OperationalError as e:
                            if 'duplicate column' not in str(e).lower() and 'already exists' not in str(e).lower():
                                logger.error(f"Migration error: {e}")
                    
                    conn.commit()
                    logger.info(f"✅ Migration applied successfully! ({applied_count} statements executed)")
                else:
                    logger.error("❌ Migration file not found!")
            else:
                logger.info("✅ Database schema is up to date")
            
            conn.close()
        
        logger.info(f"✅ {settings.app_name} started successfully")
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
        # Disconnect from Redis
        await redis_client.disconnect()
        logger.info("Redis disconnected")
        
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Resume upload form"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("auth/register.html", {"request": request})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page"""
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Reset password page"""
    return templates.TemplateResponse("auth/reset_password.html", {"request": request})

@app.get("/resumes", response_class=HTMLResponse)
async def resumes_list_page(request: Request):
    """Resume list page"""
    return templates.TemplateResponse("resumes/list.html", {"request": request})

@app.get("/resumes/upload-new", response_class=HTMLResponse)
async def resume_upload_new_page(request: Request):
    """New resume upload page"""
    return templates.TemplateResponse("resumes/upload_new.html", {"request": request})

@app.get("/candidates", response_class=HTMLResponse)
async def candidates_list_page(request: Request):
    """Candidates list page"""
    return templates.TemplateResponse("candidates/list.html", {"request": request})

@app.get("/candidates/{candidate_id}", response_class=HTMLResponse)
async def candidate_detail_page(request: Request, candidate_id: str):
    """Candidate detail page"""
    return templates.TemplateResponse("candidates/detail.html", {"request": request})

@app.get("/candidates/{candidate_id}/edit", response_class=HTMLResponse)
async def candidate_edit_page(request: Request, candidate_id: str):
    """Candidate edit page"""
    return templates.TemplateResponse("candidates/edit.html", {"request": request, "candidate_id": candidate_id})

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_list_page(request: Request):
    """Jobs list page"""
    return templates.TemplateResponse("jobs/job_list.html", {"request": request})

@app.get("/debug-auth", response_class=HTMLResponse)
async def debug_auth_page(request: Request):
    """Debug authentication page"""
    return templates.TemplateResponse("debug_auth.html", {"request": request})

@app.get("/make-admin", response_class=HTMLResponse)
async def make_admin_page(request: Request):
    """Make user admin page"""
    return templates.TemplateResponse("make_admin.html", {"request": request})

@app.get("/jobs/create", response_class=HTMLResponse)
async def job_create_page(request: Request):
    """Job creation page"""
    return templates.TemplateResponse("jobs/job_create.html", {"request": request})

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail_page(request: Request, job_id: str):
    """Job detail page"""
    return templates.TemplateResponse("jobs/job_detail.html", {"request": request, "job_id": job_id})

@app.get("/jobs/{job_id}/edit", response_class=HTMLResponse)
async def job_edit_page(request: Request, job_id: str):
    """Job edit page"""
    return templates.TemplateResponse("jobs/job_edit.html", {"request": request, "job_id": job_id})

@app.get("/jobs-management/dashboard", response_class=HTMLResponse)
async def jobs_management_dashboard_page(request: Request):
    """Jobs Management dashboard page"""
    return templates.TemplateResponse("jobs_management/dashboard.html", {"request": request})

@app.get("/jobs-management/{job_id}/analytics", response_class=HTMLResponse)
async def jobs_analytics_page(request: Request, job_id: str):
    """Job analytics page"""
    return templates.TemplateResponse("jobs_management/analytics.html", {"request": request, "job_id": job_id})

@app.get("/jobs-management/{job_id}/audit-log", response_class=HTMLResponse)
async def jobs_audit_log_page(request: Request, job_id: str):
    """Job audit log page"""
    return templates.TemplateResponse("jobs_management/audit_log.html", {"request": request, "job_id": job_id})

@app.get("/setup-check", response_class=HTMLResponse)
async def setup_check_page(request: Request):
    """Database setup checker page"""
    return templates.TemplateResponse("setup_check.html", {"request": request})

@app.get("/users", response_class=HTMLResponse)
async def users_dashboard_page(request: Request):
    """User Management dashboard page"""
    import time
    return templates.TemplateResponse("users/dashboard.html", {
        "request": request,
        "cache_bust": int(time.time())  # Force browser to reload JS
    })

@app.get("/users/{user_id}", response_class=HTMLResponse)
async def user_detail_page(request: Request, user_id: str):
    """User detail page"""
    return templates.TemplateResponse("users/detail.html", {"request": request, "user_id": user_id})

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

        # Analyze resume authenticity using real criteria
        authenticity_analysis = resume_analyzer.analyze_authenticity(text_content, structure_info)

        authenticity_score = AuthenticityScore(
            overall_score=authenticity_analysis['overall_score'],
            font_consistency=authenticity_analysis['font_consistency'],
            grammar_score=authenticity_analysis['grammar_score'],
            formatting_score=authenticity_analysis['formatting_score'],
            visual_consistency=authenticity_analysis['visual_consistency'],
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
    files: List[UploadFile] = File(...)
):
    """Batch scan multiple resumes with async processing"""
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
                result = await scan_resume(request, file, job_description=None)
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

@app.post("/api/setup/initial-admin")
async def create_initial_admin():
    """Create initial admin user - NO AUTHENTICATION REQUIRED"""
    from core.database import get_db
    from models.database import User
    from services.password_service import PasswordService
    from sqlalchemy import select
    import uuid
    from datetime import datetime
    
    try:
        db = None
        async for session in get_db():
            db = session
            break
        
        if not db:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if any users exist
        result = await db.execute(select(User))
        existing_users = result.scalars().all()
        
        if len(existing_users) > 0:
            return {
                "message": "Users already exist. Initial setup not allowed.",
                "user_count": len(existing_users)
            }
        
        # Create admin user
        password_service = PasswordService()
        password_hash = password_service.hash_password("Admin@123")
        
        admin_user = User(
            id=str(uuid.uuid4()),
            full_name="Admin User",
            email="admin@example.com",
            password_hash=password_hash,
            role="admin",
            status="active",
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        await db.commit()
        
        return {
            "message": "Initial admin user created successfully",
            "email": "admin@example.com",
            "password": "Admin@123",
            "note": "Please change this password after login"
        }
        
    except Exception as e:
        logger.error(f"Error creating initial admin: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create admin user: {str(e)}")

@app.post("/api/setup/apply-migration")
async def apply_migration_api():
    """Apply database migration via API"""
    import sqlite3
    import os
    
    try:
        db_path = "hr_recruitment.db"
        sql_file = "migrations/010_create_user_management_tables.sql"
        
        if not os.path.exists(sql_file):
            raise HTTPException(status_code=404, detail="Migration file not found")
        
        # Read migration SQL
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Apply migration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Split and execute statements
        statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')]
        
        results = []
        for statement in statements:
            try:
                cursor.execute(statement)
                if 'CREATE TABLE' in statement.upper():
                    table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                    results.append(f"Created table: {table_name}")
                elif 'ALTER TABLE' in statement.upper() and 'ADD COLUMN' in statement.upper():
                    results.append("Added column to users table")
            except sqlite3.OperationalError as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    results.append(f"Skipped (already exists): {str(e)}")
                else:
                    results.append(f"Warning: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Migration applied successfully!",
            "details": results
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/api/setup/check-database")
async def check_database():
    """Check database setup status"""
    import sqlite3
    import os
    
    try:
        db_path = "hr_recruitment.db"
        if not os.path.exists(db_path):
            return {
                "database_exists": False,
                "error": "Database file not found",
                "action_needed": "Run: python apply_migration.py migrations/010_create_user_management_tables.sql"
            }
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table_exists = cursor.fetchone() is not None
        
        # Check if users table has status column
        has_status_column = False
        if users_table_exists:
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            has_status_column = 'status' in columns
        
        # Check if admin user exists
        admin_exists = False
        if users_table_exists:
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'admin@example.com'")
            admin_exists = cursor.fetchone()[0] > 0
        
        conn.close()
        
        status = {
            "database_exists": True,
            "users_table_exists": users_table_exists,
            "status_column_exists": has_status_column,
            "admin_user_exists": admin_exists,
            "migration_needed": not has_status_column,
            "columns": columns if users_table_exists else []
        }
        
        if not has_status_column:
            status["action_needed"] = "Run: python apply_migration.py migrations/010_create_user_management_tables.sql"
        elif not admin_exists:
            status["action_needed"] = "Run: python create_admin_user.py OR use POST /api/setup/initial-admin"
        else:
            status["status"] = "ready"
            status["action_needed"] = "None - system is ready!"
        
        return status
        
    except Exception as e:
        return {
            "error": str(e),
            "traceback": str(e.__class__.__name__)
        }

@app.post("/api/setup/create-user-no-auth")
async def create_user_no_auth(user_data: dict):
    """TEMPORARY: Create user without authentication for debugging"""
    import sqlite3
    
    # CRITICAL: Fix database schema FIRST before any SQLAlchemy operations
    try:
        db_path = "hr_recruitment.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if status column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            logger.info("🔧 Applying missing columns to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(50) DEFAULT 'active'")
            cursor.execute("ALTER TABLE users ADD COLUMN deactivation_reason TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN last_activity_at TIMESTAMP")
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP")
            conn.commit()
            logger.info("✅ Database schema updated successfully!")
        
        conn.close()
    except sqlite3.OperationalError as e:
        if 'duplicate column' not in str(e).lower():
            logger.error(f"Schema fix error: {e}")
            raise HTTPException(status_code=500, detail=f"Database schema error: {str(e)}")
    except Exception as e:
        logger.error(f"Database check error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # NOW import and use SQLAlchemy
    from core.database import get_db
    from models.database import User
    from services.password_service import PasswordService
    from sqlalchemy import select, func
    import uuid
    from datetime import datetime
    
    try:
        db = None
        async for session in get_db():
            db = session
            break
        
        # Check if email already exists
        result = await db.execute(
            select(User).where(func.lower(User.email) == user_data.get("email", "").lower())
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
        
        # Get admin user as creator (optional - create if doesn't exist)
        admin_result = await db.execute(select(User).where(User.email == "admin@example.com"))
        admin_user = admin_result.scalar_one_or_none()
        
        # If no admin exists, create one first
        if not admin_user:
            logger.info("Creating initial admin user...")
            password_service_temp = PasswordService()
            admin_user = User(
                id=str(uuid.uuid4()),
                full_name="Admin User",
                email="admin@example.com",
                password_hash=password_service_temp.hash_password("Admin@123"),
                role="admin",
                status="active",
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(admin_user)
            await db.flush()
            logger.info("✅ Admin user created automatically!")
        
        # Generate password
        password_service = PasswordService()
        temp_password = user_data.get("temp_password", "TempPass@123")
        password_hash = password_service.hash_password(temp_password)
        
        # Create user
        new_user = User(
            id=str(uuid.uuid4()),
            full_name=user_data.get("full_name"),
            email=user_data.get("email"),
            mobile=user_data.get("mobile"),
            password_hash=password_hash,
            role=user_data.get("role", "recruiter"),
            department=user_data.get("department"),
            status="active",
            is_active=True,
            email_verified=True,
            created_by=admin_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_user)
        await db.commit()
        
        return {
            "message": "User created successfully",
            "id": new_user.id,
            "email": new_user.email,
            "temporary_password": temp_password
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

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
