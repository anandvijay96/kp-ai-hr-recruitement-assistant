from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uuid
from typing import List
import logging
import aiofiles

from core.config import settings
from models.schemas import ResumeAnalysis, JobDescription, AuthenticityScore, MatchingScore
from services.document_processor import DocumentProcessor
from services.resume_analyzer import ResumeAuthenticityAnalyzer

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
        # Validate file
        if not file.filename.lower().endswith(tuple(settings.allowed_extensions)):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
            )

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.upload_dir, safe_filename)

        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Process document
        text_content = document_processor.extract_text(file_path)
        structure_info = document_processor.analyze_document_structure(file_path)

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

        # TODO: Implement JD matching if provided
        matching_score = None
        if job_description:
            matching_score = MatchingScore(
                overall_match=75.0,  # Placeholder
                skills_match=80.0,
                experience_match=70.0,
                education_match=75.0
            )

        # Create analysis result
        analysis = ResumeAnalysis(
            id=file_id,
            filename=file.filename,
            file_size=len(content),
            authenticity_score=authenticity_score,
            matching_score=matching_score
        )

        return analysis

    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-scan")
async def batch_scan_resumes(
    request: Request,
    files: List[UploadFile] = File(...)
):
    """Batch scan multiple resumes"""
    try:
        results = []
        errors = []

        for file in files:
            try:
                # Reuse single file logic
                result = await scan_resume(request, file)
                results.append(result)
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")

        return {
            "total_processed": len(files),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
