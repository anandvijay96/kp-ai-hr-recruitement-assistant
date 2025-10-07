from pydantic import BaseModel
from typing import List, Optional

class CandidateFilter(BaseModel):
    skills: Optional[List[str]] = None
    skills_logic: str = 'AND'
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    education: Optional[List[str]] = None
    location: Optional[str] = None
    rating_min: Optional[float] = None
    status: Optional[List[str]] = None
    search_query: Optional[str] = None

class FilterPresetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    filters: CandidateFilter
    is_shared: bool = False

class FilterPresetResponse(FilterPresetCreate):
    id: int
