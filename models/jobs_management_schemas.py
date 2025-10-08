"""Pydantic schemas for Jobs Management feature"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class JobManagementStatus(str, Enum):
    """Extended job status for management"""
    DRAFT = "draft"
    OPEN = "open"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ExternalPortal(str, Enum):
    """External job portals"""
    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    INDEED = "indeed"


class PostingStatus(str, Enum):
    """External posting status"""
    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"
    EXPIRED = "expired"


class BulkOperationType(str, Enum):
    """Bulk operation types"""
    STATUS_UPDATE = "status_update"
    ARCHIVE = "archive"
    UPDATE_DEADLINE = "update_deadline"
    ASSIGN_RECRUITER = "assign_recruiter"


class BulkOperationStatus(str, Enum):
    """Bulk operation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class AuditActionType(str, Enum):
    """Audit log action types"""
    CREATE = "create"
    UPDATE = "update"
    STATUS_CHANGE = "status_change"
    DELETE = "delete"
    BULK_UPDATE = "bulk_update"
    EXTERNAL_POST = "external_post"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class JobStatusUpdateRequest(BaseModel):
    """Request to update job status"""
    status: JobManagementStatus
    reason: Optional[str] = Field(None, max_length=500, description="Reason for status change")


class ExternalPostingRequest(BaseModel):
    """Request to post job to external portals"""
    portals: List[ExternalPortal] = Field(..., min_items=1, description="List of portals to post to")
    field_mappings: Optional[Dict[str, Dict[str, Any]]] = Field(
        default={},
        description="Portal-specific field mappings"
    )
    expires_in_days: int = Field(
        default=30,
        ge=1,
        le=90,
        description="Number of days until posting expires"
    )


class BulkUpdateRequest(BaseModel):
    """Request for bulk job updates"""
    job_ids: List[str] = Field(..., min_items=1, max_items=50, description="List of job IDs")
    operation: BulkOperationType = Field(..., description="Type of bulk operation")
    parameters: Dict[str, Any] = Field(..., description="Operation-specific parameters")
    dry_run: bool = Field(default=False, description="Preview changes without applying")
    
    @validator('job_ids')
    def validate_job_ids(cls, v):
        """Validate job IDs list"""
        if len(v) > 50:
            raise ValueError("Maximum 50 jobs allowed per bulk operation")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate job IDs found")
        return v


class DashboardFilters(BaseModel):
    """Dashboard filter parameters"""
    status: Optional[JobManagementStatus] = None
    department: Optional[str] = None
    hiring_manager_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search: Optional[str] = Field(None, max_length=200)
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class AnalyticsRequest(BaseModel):
    """Request for job analytics"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class JobSummaryModel(BaseModel):
    """Job summary for dashboard"""
    id: str
    uuid: str
    title: str
    department: Optional[str]
    status: str
    posted_date: Optional[datetime]
    application_deadline: Optional[datetime]
    application_count: int = 0
    avg_match_score: Optional[float]
    hiring_manager: Optional[Dict[str, Any]]
    external_postings: List[str] = []
    last_updated: datetime
    view_count: int = 0
    
    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """Dashboard summary statistics"""
    total_jobs: int
    open: int = 0
    closed: int = 0
    on_hold: int = 0
    archived: int = 0
    draft: int = 0


class PaginationModel(BaseModel):
    """Pagination information"""
    total: int
    page: int
    limit: int
    total_pages: int


class DashboardResponse(BaseModel):
    """Dashboard API response"""
    success: bool = True
    jobs: List[JobSummaryModel]
    pagination: PaginationModel
    summary: DashboardSummary


class FunnelMetrics(BaseModel):
    """Funnel metrics for analytics"""
    views: int
    applications: int
    shortlisted: int
    interviewed: int
    offers: int
    hires: int


class ConversionRates(BaseModel):
    """Conversion rates between funnel stages"""
    view_to_application: float
    application_to_shortlist: float
    shortlist_to_interview: float
    interview_to_offer: float
    offer_to_hire: float


class QualityMetrics(BaseModel):
    """Quality metrics for analytics"""
    avg_match_score: Optional[float]
    median_match_score: Optional[float]
    match_score_distribution: Dict[str, int]


class TimeMetrics(BaseModel):
    """Time-based metrics"""
    time_to_fill_days: Optional[int]
    time_to_first_application_hours: Optional[int]
    avg_time_to_shortlist_days: Optional[int]


class TrendDataPoint(BaseModel):
    """Single data point in trend chart"""
    date: str
    applications: int
    views: int


class ComparisonMetrics(BaseModel):
    """Comparison with similar jobs"""
    similar_jobs_avg_match_score: Optional[float]
    similar_jobs_avg_time_to_fill: Optional[int]


class JobAnalyticsResponse(BaseModel):
    """Job analytics API response"""
    success: bool = True
    job_id: str
    date_range: Dict[str, str]
    funnel: FunnelMetrics
    conversion_rates: ConversionRates
    quality_metrics: QualityMetrics
    time_metrics: TimeMetrics
    trends: List[TrendDataPoint]
    comparison: ComparisonMetrics


class ExternalPostingModel(BaseModel):
    """External posting details"""
    id: str
    portal: str
    external_job_id: Optional[str]
    status: str
    posted_at: Optional[datetime]
    expires_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class BulkOperationResponse(BaseModel):
    """Bulk operation status response"""
    success: bool = True
    operation_id: str
    status: str
    total_count: int
    success_count: int
    failure_count: int
    error_details: List[Dict[str, Any]] = []
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: str
    action_type: str
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    user: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Audit log API response"""
    success: bool = True
    audit_entries: List[AuditLogEntry]
    pagination: PaginationModel


class StandardResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
