"""Pydantic schemas for vendor management"""
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


# ============================================================================
# ENUMS
# ============================================================================

class VendorStatus(str, Enum):
    """Vendor status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on-hold"
    BLACKLISTED = "blacklisted"


class ServiceCategory(str, Enum):
    """Service category enumeration"""
    RECRUITMENT = "Recruitment"
    TRAINING = "Training"
    STAFFING = "Staffing"
    CONSULTING = "Consulting"
    BACKGROUND_VERIFICATION = "Background Verification"
    PAYROLL = "Payroll"
    OTHER = "Other"


class ContractStatus(str, Enum):
    """Contract status enumeration"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ApprovalStatus(str, Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ComplianceStatus(str, Enum):
    """Compliance status enumeration"""
    PENDING = "pending"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"


class DocumentStatus(str, Enum):
    """Document status enumeration"""
    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


class VerificationStatus(str, Enum):
    """Verification status enumeration"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CommunicationType(str, Enum):
    """Communication type enumeration"""
    MEETING = "meeting"
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    VIDEO_CALL = "video_call"
    SITE_VISIT = "site_visit"
    OTHER = "other"


class NotificationPriority(str, Enum):
    """Notification priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Notification type enumeration"""
    CONTRACT_EXPIRY = "contract_expiry"
    DOCUMENT_EXPIRY = "document_expiry"
    REVIEW_DUE = "review_due"
    COMPLIANCE_ALERT = "compliance_alert"
    GENERAL = "general"


class AssignmentStatus(str, Enum):
    """Assignment status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# VENDOR SCHEMAS
# ============================================================================

class VendorBase(BaseModel):
    """Base vendor schema"""
    name: str = Field(..., min_length=2, max_length=255)
    service_category: ServiceCategory
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)
    alternate_contact: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    tax_id: Optional[str] = Field(None, max_length=100)


class VendorCreateRequest(VendorBase):
    """Vendor creation request"""
    vendor_manager_id: str = Field(..., description="ID of the user managing this vendor")


class VendorUpdateRequest(BaseModel):
    """Vendor update request"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    service_category: Optional[ServiceCategory] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    alternate_contact: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    tax_id: Optional[str] = Field(None, max_length=100)
    status: Optional[VendorStatus] = None
    vendor_manager_id: Optional[str] = None


class VendorDeactivateRequest(BaseModel):
    """Vendor deactivation request"""
    reason: str = Field(..., min_length=10, max_length=500)


class VendorResponse(VendorBase):
    """Vendor response schema"""
    id: str
    vendor_code: str
    status: VendorStatus
    overall_rating: Optional[str] = None
    total_contracts: int
    active_contracts: int
    compliance_status: ComplianceStatus
    vendor_manager_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VendorDetailResponse(VendorResponse):
    """Detailed vendor response with relationships"""
    vendor_manager: Optional[Dict[str, Any]] = None
    recent_contracts: List[Dict[str, Any]] = Field(default_factory=list)
    recent_reviews: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_documents: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    """Vendor list response with pagination"""
    vendors: List[VendorResponse]
    pagination: Dict[str, int]


# ============================================================================
# CONTRACT SCHEMAS
# ============================================================================

class ContractBase(BaseModel):
    """Base contract schema"""
    contract_type: str = Field(..., max_length=100)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    contract_value: Optional[str] = Field(None, description="Contract value as string")
    currency: str = Field(default="USD", max_length=10)
    start_date: date
    end_date: date
    payment_terms: Optional[str] = None
    renewal_terms: Optional[str] = None
    auto_renew: bool = False
    renewal_notice_days: int = Field(default=90, ge=0, le=365)
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class ContractCreateRequest(ContractBase):
    """Contract creation request"""
    vendor_id: str
    file_url: str = Field(..., description="URL/path to contract document")
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = None


class ContractUpdateRequest(BaseModel):
    """Contract update request"""
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    contract_value: Optional[str] = None
    payment_terms: Optional[str] = None
    renewal_terms: Optional[str] = None
    status: Optional[ContractStatus] = None
    auto_renew: Optional[bool] = None


class ContractResponse(BaseModel):
    """Contract response schema"""
    id: str
    vendor_id: str
    contract_number: str
    contract_type: str
    title: str
    status: ContractStatus
    approval_status: ApprovalStatus
    start_date: date
    end_date: date
    contract_value: Optional[str] = None
    currency: str
    auto_renew: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContractDetailResponse(ContractResponse):
    """Detailed contract response"""
    description: Optional[str] = None
    payment_terms: Optional[str] = None
    renewal_terms: Optional[str] = None
    file_url: str
    file_name: Optional[str] = None
    version: int
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# PERFORMANCE REVIEW SCHEMAS
# ============================================================================

class PerformanceReviewBase(BaseModel):
    """Base performance review schema"""
    review_period: str = Field(..., max_length=50)
    review_type: str = Field(..., max_length=50)
    service_quality_rating: int = Field(..., ge=1, le=5)
    timeliness_rating: int = Field(..., ge=1, le=5)
    communication_rating: int = Field(..., ge=1, le=5)
    cost_effectiveness_rating: int = Field(..., ge=1, le=5)
    compliance_rating: int = Field(..., ge=1, le=5)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    recommendations: Optional[str] = None
    written_feedback: Optional[str] = None


class PerformanceReviewCreateRequest(PerformanceReviewBase):
    """Performance review creation request"""
    vendor_id: str
    review_date: date


class PerformanceReviewUpdateRequest(BaseModel):
    """Performance review update request"""
    service_quality_rating: Optional[int] = Field(None, ge=1, le=5)
    timeliness_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    cost_effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)
    compliance_rating: Optional[int] = Field(None, ge=1, le=5)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    recommendations: Optional[str] = None
    written_feedback: Optional[str] = None


class PerformanceReviewResponse(BaseModel):
    """Performance review response schema"""
    id: str
    vendor_id: str
    review_period: str
    review_date: date
    review_type: str
    overall_rating: str
    status: str
    reviewed_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PerformanceReviewDetailResponse(PerformanceReviewResponse):
    """Detailed performance review response"""
    service_quality_rating: int
    timeliness_rating: int
    communication_rating: int
    cost_effectiveness_rating: int
    compliance_rating: int
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    recommendations: Optional[str] = None
    written_feedback: Optional[str] = None
    finalized_by: Optional[str] = None
    finalized_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# COMPLIANCE DOCUMENT SCHEMAS
# ============================================================================

class ComplianceDocumentBase(BaseModel):
    """Base compliance document schema"""
    document_type: str = Field(..., max_length=100)
    document_name: str = Field(..., min_length=2, max_length=255)
    document_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class ComplianceDocumentCreateRequest(ComplianceDocumentBase):
    """Compliance document creation request"""
    vendor_id: str
    file_url: str = Field(..., description="URL/path to document file")
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = None


class ComplianceDocumentUpdateRequest(BaseModel):
    """Compliance document update request"""
    document_name: Optional[str] = Field(None, min_length=2, max_length=255)
    expiry_date: Optional[date] = None
    status: Optional[DocumentStatus] = None
    verification_status: Optional[VerificationStatus] = None
    notes: Optional[str] = None


class ComplianceDocumentResponse(BaseModel):
    """Compliance document response schema"""
    id: str
    vendor_id: str
    document_type: str
    document_name: str
    status: DocumentStatus
    verification_status: VerificationStatus
    expiry_date: Optional[date] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# COMMUNICATION SCHEMAS
# ============================================================================

class CommunicationCreateRequest(BaseModel):
    """Communication creation request"""
    vendor_id: str
    communication_type: CommunicationType
    communication_date: datetime
    subject: str = Field(..., min_length=2, max_length=255)
    details: Optional[str] = None
    attendees: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    follow_up_notes: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=255)
    is_important: bool = False


class CommunicationResponse(BaseModel):
    """Communication response schema"""
    id: str
    vendor_id: str
    communication_type: CommunicationType
    communication_date: datetime
    subject: str
    follow_up_required: bool
    is_important: bool
    logged_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# JOB ASSIGNMENT SCHEMAS
# ============================================================================

class JobAssignmentCreateRequest(BaseModel):
    """Job assignment creation request"""
    vendor_id: str
    job_id: str
    contract_id: Optional[str] = None
    assignment_date: date
    fee_structure: Optional[str] = Field(None, max_length=100)
    fee_amount: Optional[str] = None
    notes: Optional[str] = None


class JobAssignmentUpdateRequest(BaseModel):
    """Job assignment update request"""
    status: Optional[AssignmentStatus] = None
    candidates_submitted: Optional[int] = Field(None, ge=0)
    candidates_hired: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class JobAssignmentResponse(BaseModel):
    """Job assignment response schema"""
    id: str
    vendor_id: str
    job_id: str
    assignment_date: date
    status: AssignmentStatus
    candidates_submitted: int
    candidates_hired: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD & ANALYTICS SCHEMAS
# ============================================================================

class VendorDashboardResponse(BaseModel):
    """Vendor dashboard statistics"""
    total_vendors: int
    active_vendors: int
    inactive_vendors: int
    blacklisted_vendors: int
    total_contracts: int
    active_contracts: int
    expiring_contracts: int
    expired_documents: int
    pending_reviews: int
    compliance_alerts: int


class VendorAnalyticsResponse(BaseModel):
    """Vendor analytics response"""
    vendor_id: str
    date: date
    total_jobs_assigned: int
    active_jobs: int
    candidates_submitted: int
    candidates_interviewed: int
    candidates_hired: int
    total_revenue: str
    average_rating: Optional[str] = None
    response_time_hours: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationResponse(BaseModel):
    """Notification response schema"""
    id: str
    vendor_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    is_read: bool
    deadline: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# BULK OPERATION SCHEMAS
# ============================================================================

class BulkVendorOperationRequest(BaseModel):
    """Bulk vendor operation request"""
    vendor_ids: List[str] = Field(..., min_length=1)
    operation: str = Field(..., description="Operation type: change_manager, update_status, deactivate")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BulkVendorOperationResponse(BaseModel):
    """Bulk vendor operation response"""
    operation_id: str
    total_count: int
    success_count: int
    failure_count: int
    status: str
    errors: List[Dict[str, Any]] = Field(default_factory=list)
