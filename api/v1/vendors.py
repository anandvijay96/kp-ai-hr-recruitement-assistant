"""Vendor Management API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.database import get_db
from core.auth import get_current_user
from models.database import User
from models.vendor_models import Vendor, CandidateVendor
from models.vendor_schemas import (
    VendorCreate, VendorUpdate, VendorResponse, VendorListResponse,
    VendorFilter, CandidateVendorCreate, CandidateVendorUpdate,
    CandidateVendorResponse, VendorStatistics
)
from services.vendor_service import VendorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/vendors", tags=["vendors"])


# ============================================================================
# VENDOR CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=Dict[str, Any])
async def list_vendors(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    vendor_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """List all vendors with filtering and pagination"""
    try:
        service = VendorService(db)
        
        # Build filter
        filters = VendorFilter(
            search_query=search,
            status=[status] if status else None,
            vendor_type=[vendor_type] if vendor_type else None
        )
        
        result = await service.search_vendors(filters, page, page_size)
        return result
        
    except Exception as e:
        logger.error(f"Error listing vendors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=VendorResponse)
async def create_vendor(
    vendor_data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new vendor"""
    try:
        service = VendorService(db)
        vendor = await service.create_vendor(vendor_data, current_user.id)
        
        # Convert SQLAlchemy object to dict properly
        vendor_data = {
            'id': vendor.id,
            'company_name': vendor.company_name,
            'vendor_type': vendor.vendor_type,
            'industry': vendor.industry,
            'website': vendor.website,
            'description': vendor.description,
            'contact_person': vendor.contact_person,
            'contact_email': vendor.contact_email,
            'contact_phone': vendor.contact_phone,
            'address': vendor.address,
            'city': vendor.city,
            'state': vendor.state,
            'country': vendor.country,
            'postal_code': vendor.postal_code,
            'status': vendor.status,
            'commission_rate': vendor.commission_rate,
            'payment_terms': vendor.payment_terms,
            'notes': vendor.notes,
            'tags': vendor.tags,
            'created_at': vendor.created_at,
            'updated_at': vendor.updated_at,
            'created_by': vendor.created_by,
            'candidates_count': 0,
            'active_candidates_count': 0
        }
        
        return VendorResponse(**vendor_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vendor details"""
    try:
        service = VendorService(db)
        vendor = await service.get_vendor(vendor_id)
        
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Get counts
        candidates_count = await service._get_vendor_candidate_count(vendor_id)
        active_candidates_count = await service._get_vendor_active_candidate_count(vendor_id)
        
        return VendorResponse(
            **vendor.__dict__,
            candidates_count=candidates_count,
            active_candidates_count=active_candidates_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    vendor_data: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update vendor"""
    try:
        service = VendorService(db)
        vendor = await service.update_vendor(vendor_id, vendor_data, current_user.id)
        
        # Get counts
        candidates_count = await service._get_vendor_candidate_count(vendor_id)
        active_candidates_count = await service._get_vendor_active_candidate_count(vendor_id)
        
        return VendorResponse(
            **vendor.__dict__,
            candidates_count=candidates_count,
            active_candidates_count=active_candidates_count
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (soft delete) vendor"""
    try:
        service = VendorService(db)
        await service.delete_vendor(vendor_id, current_user.id)
        
        return {"success": True, "message": "Vendor deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CANDIDATE-VENDOR LINKING ENDPOINTS
# ============================================================================

@router.post("/{vendor_id}/candidates", response_model=CandidateVendorResponse)
async def link_candidate_to_vendor(
    vendor_id: str,
    candidate_id: str = Query(...),
    link_data: Optional[CandidateVendorCreate] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a candidate to a vendor"""
    try:
        service = VendorService(db)
        
        # If no link_data provided, create basic link
        if not link_data:
            link_data = CandidateVendorCreate(
                candidate_id=candidate_id,
                vendor_id=vendor_id
            )
        else:
            link_data.vendor_id = vendor_id
            link_data.candidate_id = candidate_id
        
        link = await service.link_candidate_to_vendor(link_data, current_user.id)
        
        return CandidateVendorResponse(**link.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error linking candidate to vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vendor_id}/candidates", response_model=List[CandidateVendorResponse])
async def get_vendor_candidates(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all candidates linked to a vendor"""
    try:
        service = VendorService(db)
        candidates = await service.get_vendor_candidates(vendor_id)
        
        return [CandidateVendorResponse(**c.__dict__) for c in candidates]
    except Exception as e:
        logger.error(f"Error getting vendor candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/candidate-links/{link_id}", response_model=CandidateVendorResponse)
async def update_candidate_vendor_link(
    link_id: str,
    link_data: CandidateVendorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update candidate-vendor relationship"""
    try:
        service = VendorService(db)
        link = await service.update_candidate_vendor_link(link_id, link_data)
        
        return CandidateVendorResponse(**link.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating candidate-vendor link: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@router.get("/stats/overview", response_model=VendorStatistics)
async def get_vendor_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall vendor statistics"""
    try:
        service = VendorService(db)
        stats = await service.get_vendor_statistics()
        
        return VendorStatistics(**stats)
    except Exception as e:
        logger.error(f"Error getting vendor statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
