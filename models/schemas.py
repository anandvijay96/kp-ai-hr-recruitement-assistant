from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ResumeStatus(str, Enum):
    NEW = "new"
    SCREENED = "screened"
    INTERVIEWED = "interviewed"
    REJECTED = "rejected"
    HIRED = "hired"

class AuthenticityScore(BaseModel):
    overall_score: float = Field(..., ge=0, le=100, description="Overall authenticity score")
    font_consistency: float = Field(..., ge=0, le=100)
    grammar_score: float = Field(..., ge=0, le=100)
    formatting_score: float = Field(..., ge=0, le=100)
    visual_consistency: float = Field(..., ge=0, le=100)
    linkedin_profile_score: float = Field(default=0, ge=0, le=100)
    capitalization_score: float = Field(default=0, ge=0, le=100)
    details: List[str] = Field(default_factory=list)
    flags: List[Dict[str, str]] = Field(default_factory=list)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)

class SkillMatch(BaseModel):
    skill: str
    found: bool
    confidence: float = Field(..., ge=0, le=1)

class MatchingScore(BaseModel):
    overall_match: float = Field(..., ge=0, le=100)
    skills_match: float = Field(..., ge=0, le=100)
    experience_match: float = Field(..., ge=0, le=100)
    education_match: float = Field(..., ge=0, le=100)
    keyword_matches: List[SkillMatch] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    details: List[str] = Field(default_factory=list)

class ResumeAnalysis(BaseModel):
    id: Optional[str] = None
    filename: str
    file_size: int
    upload_date: datetime = Field(default_factory=datetime.utcnow)

    # Extracted information
    personal_info: Dict[str, Any] = Field(default_factory=dict)
    skills: List[str] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    # Analysis results
    authenticity_score: AuthenticityScore
    matching_score: Optional[MatchingScore] = None
    status: ResumeStatus = ResumeStatus.NEW

class JobDescription(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    experience_level: str
    location: Optional[str] = None
    work_type: Optional[str] = None

class BatchAnalysisResult(BaseModel):
    total_processed: int
    successful: int
    failed: int
    results: List[ResumeAnalysis] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
