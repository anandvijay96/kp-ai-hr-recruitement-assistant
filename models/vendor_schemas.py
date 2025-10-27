"""Pydantic schemas for Vendor Management"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============================================================================
# VENDOR SCHEMAS
# ============================================================================

class VendorBase(BaseModel):
    """Base vendor schema"""
    company_name: str = Field(..., min_length=2, max_length=255)
    vendor_type: Optional[str] = Field("agency", pattern="^(agency|freelancer|consultant|other)$")
    industry_specialization: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    
    # Contact Information
    contact_person: str = Field(..., min_length=2, max_length=100)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=20)
    
    # Address
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Business Terms
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=100)  # 0-100%
    payment_terms: Optional[str] = Field(None, max_length=255)
    contract_start_date: Optional[str] = Field(None, max_length=50)
    contract_end_date: Optional[str] = Field(None, max_length=50)
    
    # Settings
    has_portal_access: Optional[bool] = False
    can_submit_candidates: Optional[bool] = True
    requires_approval: Optional[bool] = True
    
    # Notes & Tags
    notes: Optional[str] = None
    tags: Optional[str] = None


class VendorCreate(VendorBase):
    """Schema for creating a vendor"""
    pass


class VendorUpdate(BaseModel):
    """Schema for updating a vendor"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    vendor_type: Optional[str] = Field(None, pattern="^(agency|freelancer|consultant|other)$")
    industry_specialization: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    
    # Contact Information
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    
    # Address
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Business Terms
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    payment_terms: Optional[str] = Field(None, max_length=255)
    contract_start_date: Optional[str] = Field(None, max_length=50)
    contract_end_date: Optional[str] = Field(None, max_length=50)
    
    # Settings
    has_portal_access: Optional[bool] = None
    can_submit_candidates: Optional[bool] = None
    requires_approval: Optional[bool] = None
    
    # Notes & Tags
    notes: Optional[str] = None
    tags: Optional[str] = None


class VendorResponse(VendorBase):
    """Schema for vendor response"""
    id: str
    status: str
    total_candidates_referred: int = 0
    candidates_hired: int = 0
    success_rate: Decimal = Decimal("0.00")
    average_rating: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    
    # Counts for list views
    candidates_count: Optional[int] = 0
    active_candidates_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    """Schema for vendor list response"""
    vendors: List[VendorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# CANDIDATE-VENDOR LINKING SCHEMAS
# ============================================================================

class CandidateVendorBase(BaseModel):
    """Base candidate-vendor linking schema"""
    referral_notes: Optional[str] = None
    candidate_status: Optional[str] = Field("referred", pattern="^(referred|screened|submitted|hired|rejected)$")
    agreed_rate: Optional[Decimal] = Field(None, ge=0)
    commission_amount: Optional[Decimal] = Field(None, ge=0)
    payment_status: Optional[str] = Field("pending", pattern="^(pending|paid|cancelled)$")
    vendor_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None


class CandidateVendorCreate(CandidateVendorBase):
    """Schema for linking a candidate to a vendor"""
    candidate_id: str
    vendor_id: str


class CandidateVendorUpdate(BaseModel):
    """Schema for updating candidate-vendor relationship"""
    referral_notes: Optional[str] = None
    candidate_status: Optional[str] = Field(None, pattern="^(referred|screened|submitted|hired|rejected)$")
    agreed_rate: Optional[Decimal] = Field(None, ge=0)
    commission_amount: Optional[Decimal] = Field(None, ge=0)
    payment_status: Optional[str] = Field(None, pattern="^(pending|paid|cancelled)$")
    payment_date: Optional[datetime] = None
    vendor_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None


class CandidateVendorResponse(CandidateVendorBase):
    """Schema for candidate-vendor relationship response"""
    id: str
    candidate_id: str
    vendor_id: str
    referral_date: datetime
    payment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# FILTER & SEARCH SCHEMAS
# ============================================================================

class VendorFilter(BaseModel):
    """Schema for filtering vendors"""
    search_query: Optional[str] = None
    status: Optional[List[str]] = None
    vendor_type: Optional[List[str]] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    has_portal_access: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class VendorStatistics(BaseModel):
    """Schema for vendor statistics"""
    total_vendors: int
    active_vendors: int
    inactive_vendors: int
    suspended_vendors: int
    total_candidates_referred: int
    total_candidates_hired: int
    overall_success_rate: Decimal
    average_vendor_rating: Optional[Decimal]
