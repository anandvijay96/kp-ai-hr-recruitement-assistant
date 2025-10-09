from fastapi import APIRouter, Depends, Body
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import io

from core.database import get_db
from services.filter_service import FilterService
from services.preset_service import PresetService
from services.candidate_service import CandidateService
from services.export_service import ExportService
from models.filter_models import CandidateFilter, FilterPresetCreate, FilterPresetResponse

router = APIRouter()

# Services that don't need database session can be instantiated globally
filter_service = FilterService()
preset_service = PresetService()
export_service = ExportService()

# CandidateService needs database session - instantiate in endpoints via dependency injection

@router.post("/search")
def search_candidates(filters: CandidateFilter, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Searches and filters candidates using database queries.
    If search_query is provided, uses full-text search with optional filters.
    """
    # If search_query is provided, use full-text search
    if filters.search_query:
        return filter_service.full_text_search(filters.search_query, db, page, page_size)
    
    # Otherwise use traditional filtering
    return filter_service.search_candidates(filters, db, page, page_size)

@router.get("/full-text-search")
def full_text_search(q: str, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Perform full-text search across all candidate data.
    
    Supports:
    - Simple search: "Python developer"
    - Boolean AND: "Python AND React"
    - Boolean OR: "Java OR Kotlin"
    - Boolean NOT: "Python NOT Django"
    - Phrase search: "senior software engineer"
    - Complex: "(Python OR Java) AND React NOT PHP"
    """
    return filter_service.full_text_search(q, db, page, page_size)

@router.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)) -> Dict[str, List]:
    """Retrieves available options for filters from the database."""
    return filter_service.get_filter_options(db)

@router.post("/filter-presets", response_model=FilterPresetResponse)
def create_filter_preset(preset_data: FilterPresetCreate, user_id: int = 1) -> FilterPresetResponse: # Assuming user_id=1 for demo
    """Saves a new filter preset."""
    return preset_service.create_preset(user_id, preset_data)

@router.get("/filter-presets", response_model=List[FilterPresetResponse])
def get_filter_presets(user_id: int = 1) -> List[FilterPresetResponse]: # Assuming user_id=1 for demo
    """Retrieves all saved filter presets for the user."""
    return preset_service.get_presets_for_user(user_id)

@router.get("/")
def get_all_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all candidates with pagination."""
    candidates = candidate_service.get_all_candidates(db, skip, limit)
    return {"candidates": candidates, "total": len(candidates)}

@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate by ID with all related data."""
    candidate = candidate_service.get_candidate_by_id(candidate_id, db)
    if not candidate:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.post("/check-duplicate")
def check_duplicate_candidate(
    email: Optional[str] = Body(None),
    phone: Optional[str] = Body(None),
    name: Optional[str] = Body(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if candidate already exists in the database.
    Returns duplicate detection results with confidence scores.
    """
    if not email and not phone and not name:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400, 
            detail="At least one of email, phone, or name must be provided"
        )
    
    return candidate_service.check_duplicate(email, phone, name, db)

@router.post("/export/csv")
def export_candidates_csv(
    filters: CandidateFilter,
    include_scores: bool = True,
    db: Session = Depends(get_db)
):
    """
    Export filtered candidates to CSV format.
    
    Args:
        filters: Filter criteria (same as search endpoint)
        include_scores: Include authenticity/match scores in export
    
    Returns:
        CSV file download
    """
    # Get filtered candidates (all results, no pagination)
    if filters.search_query:
        results = filter_service.full_text_search(filters.search_query, db, page=1, page_size=10000)
    else:
        results = filter_service.search_candidates(filters, db, page=1, page_size=10000)
    
    # Export to CSV
    csv_content = export_service.export_to_csv(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=candidates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.post("/export/excel")
def export_candidates_excel(
    filters: CandidateFilter,
    include_scores: bool = True,
    db: Session = Depends(get_db)
):
    """
    Export filtered candidates to Excel format with formatting.
    
    Args:
        filters: Filter criteria (same as search endpoint)
        include_scores: Include authenticity/match scores in export
    
    Returns:
        Excel file download
    """
    # Get filtered candidates (all results, no pagination)
    if filters.search_query:
        results = filter_service.full_text_search(filters.search_query, db, page=1, page_size=10000)
    else:
        results = filter_service.search_candidates(filters, db, page=1, page_size=10000)
    
    # Export to Excel
    excel_bytes = export_service.export_to_excel(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=candidates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )

@router.get("/export/csv")
def export_all_candidates_csv(
    include_scores: bool = True,
    db: Session = Depends(get_db)
):
    """
    Export all candidates to CSV format.
    
    Args:
        include_scores: Include authenticity/match scores in export
    
    Returns:
        CSV file download
    """
    # Get all candidates
    empty_filter = CandidateFilter()
    results = filter_service.search_candidates(empty_filter, db, page=1, page_size=10000)
    
    # Export to CSV
    csv_content = export_service.export_to_csv(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=all_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.get("/export/excel")
def export_all_candidates_excel(
    include_scores: bool = True,
    db: Session = Depends(get_db)
):
    """
    Export all candidates to Excel format.
    
    Args:
        include_scores: Include authenticity/match scores in export
    
    Returns:
        Excel file download
    """
    # Get all candidates
    empty_filter = CandidateFilter()
    results = filter_service.search_candidates(empty_filter, db, page=1, page_size=10000)
    
    # Export to Excel
    excel_bytes = export_service.export_to_excel(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    from datetime import datetime
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=all_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )
