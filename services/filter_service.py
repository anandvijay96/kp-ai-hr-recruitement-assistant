from models.filter_models import CandidateFilter
from typing import List, Dict, Any

# Mock candidate data for testing
CANDIDATE_DATA = [
    {"id": 1, "name": "John Doe", "email": "john@example.com", "skills": ["Python", "Java"], "experience_years": 5, "education": "Bachelor's", "status": "New"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "skills": ["JavaScript", "React"], "experience_years": 3, "education": "Master's", "status": "Screened"},
    {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "skills": ["Python", "SQL"], "experience_years": 7, "education": "Bachelor's", "status": "New"},
    {"id": 4, "name": "Alice Williams", "email": "alice@example.com", "skills": ["Java", "SQL"], "experience_years": 4, "education": "PhD", "status": "Interviewed"},
    {"id": 5, "name": "Charlie Brown", "email": "charlie@example.com", "skills": ["Python", "JavaScript"], "experience_years": 2, "education": "Bachelor's", "status": "New"},
]

class FilterService:
    def search_candidates(self, filters: CandidateFilter, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Filters candidates based on the provided criteria."""
        filtered_results = CANDIDATE_DATA

        if filters.skills:
            filtered_results = [c for c in filtered_results if any(skill in c.get('skills', []) for skill in filters.skills)]

        # Filter by experience
        if filters.min_experience is not None:
            filtered_results = [c for c in filtered_results if c.get('experience_years', 0) >= filters.min_experience]
        if filters.max_experience is not None:
            filtered_results = [c for c in filtered_results if c.get('experience_years', 0) <= filters.max_experience]

        # Filter by education
        if filters.education:
            filtered_results = [c for c in filtered_results if c.get('education') in filters.education]

        # Filter by location
        if filters.location:
            filtered_results = [c for c in filtered_results if c.get('location') == filters.location]

        # Filter by status
        if filters.status:
            filtered_results = [c for c in filtered_results if c.get('status') in filters.status]

        # Paginate results
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = filtered_results[start:end]

        return {
            "results": paginated_results,
            "pagination": {
                "total": len(filtered_results),
                "page": page,
                "page_size": page_size,
                "total_pages": max(1, (len(filtered_results) + page_size - 1) // page_size)
            }
        }

    def get_filter_options(self) -> Dict[str, List]:
        """Retrieves distinct values for filter options."""
        # In a real app, this would query the database for distinct skills, locations, etc.
        return {
            "skills": ["Python", "Java", "JavaScript", "SQL"],
            "locations": ["New York, NY", "San Francisco, CA", "Austin, TX"],
            "education_levels": ["Bachelor's", "Master's", "PhD"]
        }
