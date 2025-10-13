"""Pydantic schemas for client management"""
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# Enums
class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on-hold"
    ARCHIVED = "archived"


class CommunicationType(str, Enum):
    MEETING = "meeting"
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    VIDEO_CALL = "video_call"
    CONTRACT_SIGNED = "contract_signed"


class BulkClientOperation(str, Enum):
    CHANGE_ACCOUNT_MANAGER = "change_account_manager"
    DEACTIVATE = "deactivate"
    UPDATE_STATUS = "update_status"


# Request Schemas
class ClientContactCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    title: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r'^\+?[0-9\-\(\)\s]+$')
    mobile: Optional[str] = Field(None, pattern=r'^\+?[0-9\-\(\)\s]+$')
    is_primary: bool = False


class ClientCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[HttpUrl] = None
    address: Optional[str] = Field(None, max_length=1000)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    account_manager_id: str
    contacts: List[ClientContactCreate] = Field(default_factory=list, min_length=1)
    
    @validator('contacts')
    def validate_primary_contact(cls, v):
        if not v:
            raise ValueError('At least one contact is required')
        primary_count = sum(1 for contact in v if contact.is_primary)
        if primary_count == 0:
            v[0].is_primary = True
        elif primary_count > 1:
            raise ValueError('Only one contact can be primary')
        return v


class ClientUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[HttpUrl] = None
    address: Optional[str] = Field(None, max_length=1000)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    account_manager_id: Optional[str] = None
    status: Optional[ClientStatus] = None


class ClientDeactivateRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    reason_details: Optional[str] = Field(None, max_length=2000)


class CommunicationCreateRequest(BaseModel):
    communication_type: CommunicationType
    subject: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=10000)
    communication_date: datetime
    participants: List[str] = Field(default_factory=list)
    job_reference_id: Optional[str] = None
    is_important: bool = False
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    
    @validator('follow_up_date')
    def validate_follow_up_date(cls, v, values):
        if values.get('follow_up_required') and not v:
            raise ValueError('follow_up_date is required when follow_up_required is True')
        return v


class FeedbackCreateRequest(BaseModel):
    feedback_period: str = Field(..., max_length=20)
    feedback_date: date
    responsiveness_rating: int = Field(..., ge=1, le=5)
    communication_rating: int = Field(..., ge=1, le=5)
    requirements_clarity_rating: int = Field(..., ge=1, le=5)
    decision_speed_rating: int = Field(..., ge=1, le=5)
    overall_satisfaction: int = Field(..., ge=1, le=5)
    written_feedback: Optional[str] = Field(None, max_length=5000)


class BulkClientOperationRequest(BaseModel):
    client_ids: List[str] = Field(..., min_length=1, max_length=50)
    operation: BulkClientOperation
    parameters: Dict[str, Any]
    dry_run: bool = False


# Response Schemas
class ClientContactResponse(BaseModel):
    id: str
    full_name: str
    title: Optional[str]
    email: str
    phone: Optional[str]
    mobile: Optional[str]
    is_primary: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AccountManagerResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    
    class Config:
        from_attributes = True


class ClientResponse(BaseModel):
    id: str
    client_code: str
    name: str
    industry: Optional[str]
    website: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    logo_url: Optional[str]
    status: str
    account_manager: Optional[AccountManagerResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClientDetailResponse(ClientResponse):
    contacts: List[ClientContactResponse] = []
    deactivated_at: Optional[datetime]
    deactivation_reason: Optional[str]
    stats: Dict[str, Any] = {}


class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]


class ClientDashboardResponse(BaseModel):
    client: ClientDetailResponse
    stats: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    pipeline_summary: Dict[str, Any]


class CommunicationResponse(BaseModel):
    id: str
    communication_type: str
    subject: Optional[str]
    notes: Optional[str]
    communication_date: datetime
    participants: List[str]
    job_reference_id: Optional[str]
    logged_by: Dict[str, str]
    is_important: bool
    follow_up_required: bool
    follow_up_date: Optional[date]
    attachments: List[Dict[str, Any]] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommunicationListResponse(BaseModel):
    communications: List[CommunicationResponse]
    pagination: Dict[str, Any]


class FeedbackResponse(BaseModel):
    id: str
    feedback_period: str
    feedback_date: date
    responsiveness_rating: int
    communication_rating: int
    requirements_clarity_rating: int
    decision_speed_rating: int
    overall_satisfaction: int
    written_feedback: Optional[str]
    submitted_by: Dict[str, str]
    finalized_by: Optional[Dict[str, str]]
    is_finalized: bool
    finalized_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    feedback_records: List[FeedbackResponse]
    average_ratings: Dict[str, float]
    trend: str


class ClientJobResponse(BaseModel):
    id: str
    title: str
    status: str
    location_city: Optional[str]
    employment_type: str
    num_openings: int
    published_at: Optional[datetime]
    created_at: datetime
    candidates_count: int = 0
    
    class Config:
        from_attributes = True


class ClientJobListResponse(BaseModel):
    jobs: List[ClientJobResponse]
    summary: Dict[str, Any]


class ClientAnalyticsResponse(BaseModel):
    date: date
    active_jobs_count: int
    total_candidates_count: int
    screened_count: int
    shortlisted_count: int
    interviewed_count: int
    hired_count: int
    avg_time_to_fill_days: Optional[int]
    avg_candidate_quality_score: Optional[str]
    revenue_generated: Optional[str]
    
    class Config:
        from_attributes = True


class BulkClientOperationResponse(BaseModel):
    operation_id: str
    status: str
    total_count: int
    message: str


class BulkClientOperationStatusResponse(BaseModel):
    operation_id: str
    operation_type: str
    status: str
    total_count: int
    success_count: int
    failure_count: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
