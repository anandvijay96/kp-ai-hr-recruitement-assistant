"""Vendor management API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date

from core.database import get_db
from models.vendor_schemas import (
    VendorCreateRequest, VendorUpdateRequest, VendorDeactivateRequest,
    VendorResponse, VendorDetailResponse, VendorListResponse,
    VendorDashboardResponse, ContractCreateRequest, ContractResponse,
    ContractDetailResponse, PerformanceReviewCreateRequest,
    PerformanceReviewResponse, PerformanceReviewDetailResponse,
    ComplianceDocumentCreateRequest, ComplianceDocumentResponse,
    CommunicationCreateRequest, CommunicationResponse,
    JobAssignmentCreateRequest, JobAssignmentResponse,
    BulkVendorOperationRequest, BulkVendorOperationResponse
)
from services.vendor_management_service import VendorManagementService
from models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vendors", tags=["Vendor Management"])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # Simplified authentication (use proper auth in production)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


def require_role(roles: List[str]):
    """Dependency to check if user has required role"""
    async def check_role(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {roles}"
            )
        return current_user
    return check_role


# ============================================================================
# VENDOR CRUD ENDPOINTS
# ============================================================================

@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreateRequest,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(require_role(["admin", "manager"]))
):
    """
    Create a new vendor (Admin, Manager only)
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found. Please create a user first.")
        
        service = VendorManagementService(db)
        vendor = await service.create_vendor(data, current_user)
        
        # Load vendor manager
        if vendor.vendor_manager_id:
            result = await db.execute(select(User).where(User.id == vendor.vendor_manager_id))
            manager = result.scalar_one_or_none()
            vendor.vendor_manager = manager
        
        return vendor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=VendorListResponse)
async def list_vendors(
    status: Optional[str] = Query(None, description="Filter by status"),
    service_category: Optional[str] = Query(None, description="Filter by service category"),
    vendor_manager_id: Optional[str] = Query(None, description="Filter by vendor manager"),
    search: Optional[str] = Query(None, description="Search by name, code, or email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all vendors with optional filters
    
    Supports filtering by:
    - Status (active, inactive, on-hold, blacklisted)
    - Service category
    - Vendor manager
    - Search term (name, code, email)
    """
    try:
        service = VendorManagementService(db)
        result = await service.list_vendors(
            status=status,
            service_category=service_category,
            vendor_manager_id=vendor_manager_id,
            search=search,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error listing vendors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_model=VendorDashboardResponse)
async def get_vendor_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get vendor dashboard statistics
    
    Returns:
    - Total, active, inactive, blacklisted vendors
    - Contract statistics
    - Compliance alerts
    - Pending reviews
    """
    try:
        service = VendorManagementService(db)
        stats = await service.get_vendor_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting vendor dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vendor_id}", response_model=VendorDetailResponse)
async def get_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed vendor information by ID
    
    Includes:
    - Vendor details
    - Vendor manager info
    - Recent contracts
    - Recent reviews
    - Compliance documents
    """
    try:
        service = VendorManagementService(db)
        vendor = await service.get_vendor_by_id(vendor_id)
        
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Convert vendor to dict to add extra fields
        vendor_dict = {
            "id": vendor.id,
            "vendor_code": vendor.vendor_code,
            "name": vendor.name,
            "service_category": vendor.service_category,
            "contact_person": vendor.contact_person,
            "contact_email": vendor.contact_email,
            "contact_phone": vendor.contact_phone,
            "alternate_contact": vendor.alternate_contact,
            "website": vendor.website,
            "address": vendor.address,
            "city": vendor.city,
            "state": vendor.state,
            "country": vendor.country,
            "postal_code": vendor.postal_code,
            "tax_id": vendor.tax_id,
            "status": vendor.status,
            "overall_rating": vendor.overall_rating,
            "total_contracts": vendor.total_contracts,
            "active_contracts": vendor.active_contracts,
            "compliance_status": vendor.compliance_status,
            "vendor_manager_id": vendor.vendor_manager_id,
            "created_at": vendor.created_at,
            "updated_at": vendor.updated_at,
            "vendor_manager": None,
            "recent_contracts": [],
            "recent_reviews": [],
            "compliance_documents": []
        }
        
        # Load vendor manager
        if vendor.vendor_manager_id:
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.id == vendor.vendor_manager_id))
            manager = result.scalar_one_or_none()
            if manager:
                vendor_dict["vendor_manager"] = {
                    "id": manager.id,
                    "full_name": manager.full_name,
                    "email": manager.email
                }
        
        # Load recent contracts
        contracts = await service.get_vendor_contracts(vendor_id, limit=5)
        vendor_dict["recent_contracts"] = [
            {
                "id": c.id,
                "contract_number": c.contract_number,
                "title": c.title,
                "status": c.status,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat()
            }
            for c in contracts[:5]
        ]
        
        # Load recent reviews
        reviews = await service.get_vendor_reviews(vendor_id, limit=5)
        vendor_dict["recent_reviews"] = [
            {
                "id": r.id,
                "review_period": r.review_period,
                "overall_rating": r.overall_rating,
                "review_date": r.review_date.isoformat()
            }
            for r in reviews[:5]
        ]
        
        # Load compliance documents
        documents = await service.get_vendor_compliance_documents(vendor_id)
        vendor_dict["compliance_documents"] = [
            {
                "id": d.id,
                "document_type": d.document_type,
                "document_name": d.document_name,
                "status": d.status,
                "expiry_date": d.expiry_date.isoformat() if d.expiry_date else None
            }
            for d in documents[:10]
        ]
        
        return vendor_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    data: VendorUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update vendor information
    
    Allows updating:
    - Contact information
    - Address details
    - Status
    - Vendor manager
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found.")
        
        service = VendorManagementService(db)
        vendor = await service.update_vendor(vendor_id, data, current_user)
        return vendor
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{vendor_id}/deactivate", response_model=VendorResponse)
async def deactivate_vendor(
    vendor_id: str,
    data: VendorDeactivateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a vendor
    
    Requires a reason for deactivation.
    Sets vendor status to 'inactive' and records deactivation timestamp.
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found.")
        
        service = VendorManagementService(db)
        vendor = await service.deactivate_vendor(vendor_id, data, current_user)
        return vendor
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTRACT ENDPOINTS
# ============================================================================

@router.post("/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: ContractCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new vendor contract
    
    Automatically generates a unique contract number.
    Initial status is 'draft' with 'pending' approval status.
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found.")
        
        service = VendorManagementService(db)
        contract = await service.create_contract(data, current_user)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating contract: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vendor_id}/contracts", response_model=List[ContractResponse])
async def get_vendor_contracts(
    vendor_id: str,
    status: Optional[str] = Query(None, description="Filter by contract status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all contracts for a vendor
    
    Optionally filter by contract status.
    """
    try:
        service = VendorManagementService(db)
        contracts = await service.get_vendor_contracts(vendor_id, status=status)
        return contracts
    except Exception as e:
        logger.error(f"Error getting vendor contracts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PERFORMANCE REVIEW ENDPOINTS
# ============================================================================

@router.post("/reviews", response_model=PerformanceReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_performance_review(
    data: PerformanceReviewCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a performance review for a vendor
    
    Ratings are on a scale of 1-5 for:
    - Service quality
    - Timeliness
    - Communication
    - Cost effectiveness
    - Compliance
    
    Overall rating is calculated automatically.
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found.")
        
        service = VendorManagementService(db)
        review = await service.create_performance_review(data, current_user)
        return review
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating performance review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vendor_id}/reviews", response_model=List[PerformanceReviewResponse])
async def get_vendor_reviews(
    vendor_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of reviews to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance reviews for a vendor
    
    Returns most recent reviews first.
    """
    try:
        service = VendorManagementService(db)
        reviews = await service.get_vendor_reviews(vendor_id, limit=limit)
        return reviews
    except Exception as e:
        logger.error(f"Error getting vendor reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPLIANCE DOCUMENT ENDPOINTS
# ============================================================================

@router.post("/compliance-documents", response_model=ComplianceDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_document(
    data: ComplianceDocumentCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a compliance document for a vendor
    
    Document status is automatically determined based on expiry date:
    - 'valid' if expiry > 30 days
    - 'expiring_soon' if expiry <= 30 days
    - 'expired' if expiry date has passed
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found.")
        
        service = VendorManagementService(db)
        document = await service.create_compliance_document(data, current_user)
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating compliance document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vendor_id}/compliance-documents", response_model=List[ComplianceDocumentResponse])
async def get_vendor_compliance_documents(
    vendor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all compliance documents for a vendor
    
    Returns documents ordered by upload date (most recent first).
    """
    try:
        service = VendorManagementService(db)
        documents = await service.get_vendor_compliance_documents(vendor_id)
        return documents
    except Exception as e:
        logger.error(f"Error getting vendor compliance documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMMUNICATION ENDPOINTS
# ============================================================================

@router.post("/communications", response_model=CommunicationResponse, status_code=status.HTTP_201_CREATED)
async def create_communication(
    data: CommunicationCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Log a communication with a vendor
    
    Communication types:
    - Meeting
    - Phone call
    - Email
    - Video call
    - Site visit
    - Other
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found.")
        
        service = VendorManagementService(db)
        communication = await service.create_communication(data, current_user)
        return communication
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating communication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# JOB ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/job-assignments", response_model=JobAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_job_assignment(
    data: JobAssignmentCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a job to a vendor
    
    Links a job posting to a vendor for candidate sourcing.
    Can optionally reference a contract.
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found.")
        
        service = VendorManagementService(db)
        assignment = await service.create_job_assignment(data, current_user)
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
