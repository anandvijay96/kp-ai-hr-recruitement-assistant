from pydantic import BaseModel
from typing import List, Optional

class ResumeUploadResponse(BaseModel):
    job_id: str
    file_name: str
    status: str
    message: Optional[str] = None

class CandidateCreate(BaseModel):
    full_name: str
    email: str
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None

class CandidateResponse(CandidateCreate):
    id: int

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict]
