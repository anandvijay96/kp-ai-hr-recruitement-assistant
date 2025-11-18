"""Resume Formatter API endpoints (MVP stubs).

These endpoints will be expanded to call a ResumeFormatter service that
uses the existing LLM + extraction infrastructure to generate
client-ready formatted resumes.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from core.auth import get_current_user_or_redirect
from core.config import settings
from services.document_processor import DocumentProcessor
from services.resume_formatter import EZestResumeFormatter, EzestFormattedResume
from services.resume_templates import ResumeTemplate, get_available_templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume-formatter", tags=["resume-formatter"])


@router.get("/templates")
async def list_resume_templates(
    current_user: Dict[str, Any] = Depends(get_current_user_or_redirect),
) -> Dict[str, List[Dict[str, str]]]:
    """Return the list of available resume templates for the formatter.

    This powers the template dropdown on the standalone Resume Formatter
    page and is safe to call frequently.
    """

    templates: List[ResumeTemplate] = get_available_templates()
    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
            }
            for t in templates
        ]
    }


@router.post("/from-uploads")
async def format_resumes_from_uploads(
    client_name: str = Form(...),
    template_id: str = Form(...),
    files: List[UploadFile] = File(...),
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    instructions: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user_or_redirect),
) -> Dict[str, Any]:
    """Stub endpoint for formatting resumes from uploaded files.

    For now this only validates basic inputs and returns a placeholder
    response so that the frontend can be wired and tested without
    depending on the full LLM integration.
    """

    if not client_name.strip():
        raise HTTPException(status_code=400, detail="Client name is required")

    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one resume file")

    templates = {t.id: t for t in get_available_templates()}
    if template_id not in templates:
        raise HTTPException(status_code=400, detail="Unknown template_id")

    if template_id != "ezest_client_docx":
        raise HTTPException(status_code=400, detail="Only the eZest DOCX template is supported in this version")

    logger.info(
        "Resume Formatter invoked | user=%s client=%s template=%s files=%d",
        current_user.get("id"),
        client_name,
        template_id,
        len(files),
    )

    document_processor = DocumentProcessor()
    formatter = EZestResumeFormatter()

    temp_root = Path(settings.temp_dir) / "resume_formatter"
    temp_root.mkdir(parents=True, exist_ok=True)

    user_id: Optional[str]
    if isinstance(current_user, dict):
        raw_id = current_user.get("id")
        user_id = str(raw_id) if raw_id is not None else None
    else:
        raw_id = getattr(current_user, "id", None)
        user_id = str(raw_id) if raw_id is not None else None

    effective_jd_text = (jd_text or "").strip() if jd_text else ""

    if not effective_jd_text and jd_file is not None:
        try:
            jd_contents = await jd_file.read()
            if jd_contents:
                jd_ext = os.path.splitext(jd_file.filename or "")[1].lower()
                if jd_ext == ".txt":
                    effective_jd_text = jd_contents.decode("utf-8", errors="ignore")
                elif jd_ext in (".pdf", ".doc", ".docx"):
                    import uuid as _uuid

                    jd_temp_name = f"jd_{_uuid.uuid4().hex}{jd_ext}"
                    jd_temp_path = temp_root / jd_temp_name
                    async with aiofiles.open(jd_temp_path, "wb") as f:
                        await f.write(jd_contents)

                    jd_extracted = document_processor.extract_text(str(jd_temp_path))
                    if jd_extracted and "error processing document" not in jd_extracted.lower():
                        effective_jd_text = jd_extracted
        except Exception as exc:
            logger.warning("Failed to process JD file for resume formatter: %s", exc)

    results: List[Dict[str, Any]] = []

    import uuid

    for upload in files:
        if not upload.filename:
            continue

        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not allowed. Supported formats: {', '.join(settings.allowed_extensions)}",
            )

        contents = await upload.read()
        if not contents:
            raise HTTPException(status_code=400, detail=f"File '{upload.filename}' is empty.")

        temp_name = f"{uuid.uuid4().hex}{ext}"
        temp_path = temp_root / temp_name

        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(contents)

        text_content = document_processor.extract_text(str(temp_path))

        if not text_content or "error processing document" in text_content.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Unable to extract text from '{upload.filename}'. The file may be corrupted or password-protected.",
            )

        if "not available" in text_content.lower():
            raise HTTPException(
                status_code=500,
                detail="Document processing libraries not available. Please contact support.",
            )

        try:
            formatted: EzestFormattedResume = formatter.format_resume_text(
                resume_text=text_content,
                client_name=client_name,
                original_filename=upload.filename,
                user_id=user_id,
                jd_text=effective_jd_text or None,
                instructions=instructions,
            )
        except Exception as exc:
            logger.error("Failed to format resume '%s': %s", upload.filename, exc)
            raise HTTPException(status_code=500, detail="Failed to format one or more resumes. Please try again.")

        results.append(
            {
                "original_filename": formatted.original_filename,
                "candidate_name": formatted.candidate_name,
                "docx_token": formatted.docx_token,
                "docx_url": f"/api/v1/resume-formatter/download/{formatted.docx_token}",
                "pdf_url": None,
            }
        )

    if not results:
        raise HTTPException(status_code=400, detail="No valid resumes found in upload")

    return {
        "client_name": client_name,
        "template_id": template_id,
        "resume_count": len(results),
        "resumes": results,
    }


@router.get("/download/{token}")
async def download_formatted_resume(
    token: str,
    current_user: Dict[str, Any] = Depends(get_current_user_or_redirect),
) -> FileResponse:
    results_root = Path(settings.results_dir) / "resume_formatter"
    file_path = (results_root / token).resolve()

    user_id: Optional[str]
    if isinstance(current_user, dict):
        raw_id = current_user.get("id")
        user_id = str(raw_id) if raw_id is not None else None
    else:
        raw_id = getattr(current_user, "id", None)
        user_id = str(raw_id) if raw_id is not None else None

    if user_id and not token.startswith(str(user_id)):
        logger.warning("User %s attempted to access resume %s not owned by them", user_id, token)
        raise HTTPException(status_code=404, detail="File not found")

    results_root_resolved = results_root.resolve()
    if not str(file_path).startswith(str(results_root_resolved)) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Derive a user-friendly download name from the token when possible.
    download_name = "formatted_resume.docx"
    stem = file_path.stem
    if "__" in stem:
        parts = stem.split("__")
        # New pattern: <user_id>__<candidate-slug>__<client-slug>__<uuid>
        if len(parts) >= 3 and parts[1] and parts[2]:
            candidate_slug = parts[1].strip("-_") or "candidate"
            client_slug = parts[2].strip("-_") or "client"
            download_name = f"{candidate_slug}-{client_slug}.docx"
        # Backwards compatibility with older pattern: <user_id>__<candidate-slug>__<uuid>
        elif len(parts) >= 2 and parts[1]:
            candidate_slug = parts[1].strip("-_") or "candidate"
            download_name = f"{candidate_slug}.docx"

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=download_name,
    )
