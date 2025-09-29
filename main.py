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
from models.schemas import ResumeAnalysis, JobDescription, AuthenticityScore, MatchingScore
from services.document_processor import DocumentProcessor
from services.resume_analyzer import ResumeAuthenticityAnalyzer
from services.jd_matcher import JDMatcher
from services.result_storage import ResultStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Resume authenticity scanning and JD matching system",
    version="1.0.0"
)

# Mount static files
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
os.makedirs(settings.temp_dir, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Resume upload form"""
    return templates.TemplateResponse("upload.html", {"request": request})

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
            details=authenticity_analysis['details']
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
