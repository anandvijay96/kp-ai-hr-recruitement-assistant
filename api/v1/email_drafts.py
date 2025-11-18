"""Email draft generation API endpoints.

Provides endpoints for HR to generate client-ready email drafts either from
existing candidates in the database or directly from uploaded resume files.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiofiles
from dateutil import parser as date_parser
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user_or_redirect
from core.database import get_db
from models.database import Candidate, CandidateSkill, WorkExperience
from models.schemas import EmailDraftRequest, EmailDraftResponse
from services.document_processor import DocumentProcessor
from services.resume_data_extractor import ResumeDataExtractor
from services.email_draft_generator import EmailDraftGenerator
from services.email_draft_cache_redis import get_email_draft_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-drafts", tags=["email-drafts"])

email_draft_generator = EmailDraftGenerator()
document_processor = DocumentProcessor()
resume_data_extractor = ResumeDataExtractor()


@router.post("", response_model=EmailDraftResponse)
async def generate_email_draft(
    payload: EmailDraftRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_or_redirect),
    db: AsyncSession = Depends(get_db),
) -> EmailDraftResponse:
    """Generate an email draft summarising selected candidates for a client/vendor."""

    try:
        if not payload.candidate_ids:
            raise HTTPException(status_code=400, detail="At least one candidate must be selected")

        if not payload.job_description or not payload.job_description.strip():
            raise HTTPException(status_code=400, detail="Job description is required")

        stmt = select(Candidate).options(
            # Eager load related data required for summaries
            Candidate.skills,  # relationships expanded below via selectinload
            Candidate.work_experience,
        ).where(Candidate.id.in_(payload.candidate_ids))

        result = await db.execute(stmt)
        candidates: List[Candidate] = result.scalars().all()

        if not candidates:
            raise HTTPException(status_code=404, detail="No candidates found for provided IDs")

        # Prepare candidate profile payload for the LLM
        candidate_profiles: List[Dict[str, Any]] = []

        for c in candidates:
            # Collect skills safely
            skills: List[str] = []
            try:
                for cs in getattr(c, "skills", []) or []:
                    if isinstance(cs, CandidateSkill) and cs.skill and getattr(cs.skill, "name", None):
                        skills.append(cs.skill.name)
            except Exception:
                # Defensive: if relationship loading fails, skip skills
                logger.warning("Failed to load skills for candidate %s", c.id)

            # Collect high-level experience info
            experiences: List[Dict[str, Any]] = []
            try:
                for exp in getattr(c, "work_experience", []) or []:
                    if isinstance(exp, WorkExperience):
                        experiences.append(
                            {
                                "company": exp.company,
                                "title": exp.title,
                                "duration_months": exp.duration_months,
                                "is_current": exp.is_current,
                            }
                        )
            except Exception:
                logger.warning("Failed to load work experience for candidate %s", c.id)

            candidate_profiles.append(
                {
                    "id": c.id,
                    "name": c.full_name,
                    "email": c.email,
                    "location": c.location,
                    "professional_summary": c.professional_summary,
                    "skills": skills,
                    "work_experience": experiences,
                    "status": c.status,
                }
            )

        force_table = len(candidate_profiles) > 1
        allow_table_for_single = payload.include_table_for_single

        draft_data = email_draft_generator.generate_email_draft(
            client_name=payload.client_name,
            requirement_title=payload.requirement_title,
            job_code=payload.job_code,
            job_description=payload.job_description,
            candidates=candidate_profiles,
            force_table=force_table,
            allow_table_for_single=allow_table_for_single,
            signature=payload.signature,
            tone=payload.email_tone or "professional, friendly",
        )

        # Cache the generated draft for quick re-open per HR user + client + requirement
        try:
            cache = get_email_draft_cache()
            cache.save_draft(
                user_id=str(current_user.get("id")),
                client_name=payload.client_name,
                requirement_title=payload.requirement_title,
                job_code=payload.job_code,
                draft_data=draft_data,
            )
        except Exception as cache_exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to cache email draft (DB flow): %s", cache_exc)

        return EmailDraftResponse(**draft_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating email draft: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate email draft")


@router.post("/from-uploads", response_model=EmailDraftResponse)
async def generate_email_draft_from_uploads(
    client_name: str = Form(...),
    requirement_title: Optional[str] = Form(None),
    job_code: Optional[str] = Form(None),
    job_description_text: Optional[str] = Form(None),
    include_table_for_single: bool = Form(False),
    signature: Optional[str] = Form(None),
    rate_card: Optional[str] = Form(None),
    notice_period: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    detailed_summaries: bool = Form(False),
    prompt_hint: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    job_description_file: Optional[UploadFile] = File(None),
    current_user: Dict[str, Any] = Depends(get_current_user_or_redirect),
    db: AsyncSession = Depends(get_db),  # Kept for potential future use / consistency
) -> EmailDraftResponse:
    """Generate an email draft directly from uploaded resumes and a JD.

    This is a simple, standalone flow outside the main vetting pipeline. It:
    - accepts multiple resume files,
    - accepts JD as text and/or a JD document,
    - extracts lightweight candidate profiles,
    - passes them to the shared EmailDraftGenerator.
    """

    try:
        # Basic validations
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="Please upload at least one resume file")

        jd_text_final = (job_description_text or "").strip()

        # If a JD file is provided, try to extract text from it
        if job_description_file is not None and job_description_file.filename:
            temp_dir = "temp/email_assistant/jd"
            os.makedirs(temp_dir, exist_ok=True)
            jd_temp_path = os.path.join(
                temp_dir,
                f"jd_{uuid.uuid4().hex}_{job_description_file.filename}",
            )

            content = await job_description_file.read()
            async with aiofiles.open(jd_temp_path, "wb") as f:
                await f.write(content)

            extracted_jd_text = document_processor.extract_text(jd_temp_path)
            if extracted_jd_text and extracted_jd_text.strip():
                jd_text_final = extracted_jd_text.strip()

        if not jd_text_final:
            raise HTTPException(status_code=400, detail="Job description text or JD file is required")

        # Build candidate profiles from uploaded resumes
        candidate_profiles: List[Dict[str, Any]] = []
        temp_resume_dir = "temp/email_assistant/resumes"
        os.makedirs(temp_resume_dir, exist_ok=True)

        for file in files:
            if not file or not file.filename:
                continue

            content = await file.read()
            if not content:
                continue

            safe_name = file.filename.replace("/", "_").replace("\\", "_")
            temp_path = os.path.join(
                temp_resume_dir,
                f"resume_{uuid.uuid4().hex}_{safe_name}",
            )

            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(content)

            extracted_text = document_processor.extract_text(temp_path)
            extracted = resume_data_extractor.extract_all(extracted_text or "")

            # Compute approximate duration_months for each extracted work experience entry
            raw_experiences = extracted.get("work_experience") or []
            experiences: List[Dict[str, Any]] = []
            for exp in raw_experiences:
                start_raw = exp.get("start_date")
                end_raw = exp.get("end_date")
                duration_months: Optional[int] = None
                is_current = False

                try:
                    if start_raw:
                        start_dt = date_parser.parse(str(start_raw), default=datetime(2000, 1, 1))
                        end_text = str(end_raw or "Present")
                        if "present" in end_text.lower():
                            end_dt = datetime.utcnow()
                            is_current = True
                        else:
                            end_dt = date_parser.parse(end_text, default=datetime.utcnow())

                        duration_months = max(
                            0,
                            (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month),
                        )
                except Exception:
                    # If parsing fails, leave duration_months as None
                    duration_months = None

                experiences.append(
                    {
                        "company": exp.get("company"),
                        "title": exp.get("title"),
                        "duration_months": duration_months,
                        "is_current": is_current,
                    }
                )

            # Fallback: derive a display name from filename if needed
            derived_name = extracted.get("name") or os.path.splitext(file.filename)[0]

            candidate_profiles.append(
                {
                    "id": file.filename,
                    "name": derived_name,
                    "email": extracted.get("email"),
                    "location": None,
                    "professional_summary": None,
                    "skills": extracted.get("skills") or [],
                    "work_experience": experiences,
                    "status": "upload-only",
                }
            )

        if not candidate_profiles:
            raise HTTPException(
                status_code=400,
                detail="Could not extract any candidate information from the uploaded resumes",
            )

        force_table = len(candidate_profiles) > 1

        draft_data = email_draft_generator.generate_email_draft(
            client_name=client_name,
            requirement_title=requirement_title,
            job_code=job_code,
            job_description=jd_text_final,
            candidates=candidate_profiles,
            force_table=force_table,
            allow_table_for_single=include_table_for_single,
            signature=signature,
            tone="professional, friendly",
            rate_card=rate_card,
            notice_period=notice_period,
            location=location,
            detailed_summaries=detailed_summaries,
            prompt_hint=prompt_hint,
        )

        # Cache the generated draft for quick re-open per HR user + client + requirement
        try:
            cache = get_email_draft_cache()
            cache.save_draft(
                user_id=str(current_user.get("id")),
                client_name=client_name,
                requirement_title=requirement_title,
                job_code=job_code,
                draft_data=draft_data,
            )
        except Exception as cache_exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to cache email draft (upload flow): %s", cache_exc)

        return EmailDraftResponse(**draft_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating email draft from uploads: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate email draft from uploads")


@router.get("/recent", response_model=EmailDraftResponse)
async def get_recent_email_draft(
    client_name: str,
    requirement_title: Optional[str] = None,
    job_code: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_or_redirect),
) -> EmailDraftResponse:
    """Retrieve the most recent cached draft for this user + client + requirement.

    This powers quick re-open flows in the UI without re-running the full
    LLM generation if the underlying context hasn't changed.
    """

    try:
        cache = get_email_draft_cache()
        draft = cache.get_draft(
            user_id=str(current_user.get("id")),
            client_name=client_name,
            requirement_title=requirement_title,
            job_code=job_code,
        )

        if not draft:
            raise HTTPException(status_code=404, detail="No recent draft found for this client/requirement")

        return EmailDraftResponse(**draft)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving cached email draft: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve cached email draft")
