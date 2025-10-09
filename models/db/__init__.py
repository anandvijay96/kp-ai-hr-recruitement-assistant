"""
Database models for the Resume Upload & Vetting feature

NOTE: This module now re-exports models from the consolidated models/database.py
to maintain backward compatibility with code that imports from models.db
"""

# Import from consolidated models to avoid duplicate table definitions
from models.database import (
    Candidate,
    Resume,
    Education,
    WorkExperience,
    Skill,
    Certification,
    CandidateSkill as candidate_skills,  # Alias for compatibility
    DuplicateCheck,
)

__all__ = [
    'Candidate',
    'Resume',
    'Education',
    'WorkExperience',
    'Skill',
    'Certification',
    'candidate_skills',
    'DuplicateCheck',
]
