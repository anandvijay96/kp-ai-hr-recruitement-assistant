# Feature 8: Jobs Management - Technical Implementation

**Feature ID:** F008  
**Version:** 1.0  
**Date:** 2025-10-08  

---

## 1. DATABASE DESIGN

### 1.1 New Tables

#### job_analytics
```sql
CREATE TABLE job_analytics (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    view_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,
    shortlist_count INTEGER DEFAULT 0,
    interview_count INTEGER DEFAULT 0,
    offer_count INTEGER DEFAULT 0,
    hire_count INTEGER DEFAULT 0,
    avg_match_score DECIMAL(5,2),
    median_match_score DECIMAL(5,2),
    time_to_fill INTEGER,
    time_to_first_application INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, date)
);
CREATE INDEX idx_job_analytics_job_id ON job_analytics(job_id);
CREATE INDEX idx_job_analytics_date ON job_analytics(date);
```

#### job_external_postings
```sql
CREATE TABLE job_external_postings (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    portal VARCHAR(50) NOT NULL,
    external_job_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    posted_at TIMESTAMP,
    expires_at TIMESTAMP,
    error_message TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, portal)
);
CREATE INDEX idx_job_external_postings_job_id ON job_external_postings(job_id);
```

#### job_audit_log
```sql
CREATE TABLE job_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    old_values TEXT,
    new_values TEXT,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)
);
CREATE INDEX idx_job_audit_log_job_id ON job_audit_log(job_id);
CREATE INDEX idx_job_audit_log_timestamp ON job_audit_log(timestamp);
```

#### bulk_operations
```sql
CREATE TABLE bulk_operations (
    id VARCHAR(36) PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    job_ids TEXT NOT NULL,
    parameters TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_details TEXT,
    initiated_by VARCHAR(36) NOT NULL REFERENCES users(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_bulk_operations_status ON bulk_operations(status);
```

### 1.2 Modify Existing Tables

```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_deadline TIMESTAMP;
CREATE INDEX IF NOT EXISTS idx_jobs_archived_at ON jobs(archived_at);
ALTER TABLE job_status_history ADD COLUMN IF NOT EXISTS reason TEXT;
```

### 1.3 ORM Models

**File:** `models/database.py` - Add these classes:

```python
class JobAnalytics(Base):
    __tablename__ = "job_analytics"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    shortlist_count = Column(Integer, default=0)
    interview_count = Column(Integer, default=0)
    offer_count = Column(Integer, default=0)
    hire_count = Column(Integer, default=0)
    avg_match_score = Column(String(10))
    median_match_score = Column(String(10))
    time_to_fill = Column(Integer)
    time_to_first_application = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class JobExternalPosting(Base):
    __tablename__ = "job_external_postings"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    portal = Column(String(50), nullable=False)
    external_job_id = Column(String(255))
    status = Column(String(50), nullable=False)
    posted_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    metadata = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class JobAuditLog(Base):
    __tablename__ = "job_audit_log"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    old_values = Column(Text)
    new_values = Column(Text)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    checksum = Column(String(64))

class BulkOperation(Base):
    __tablename__ = "bulk_operations"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    operation_type = Column(String(50), nullable=False)
    job_ids = Column(Text, nullable=False)
    parameters = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    total_count = Column(Integer, nullable=False)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    error_details = Column(Text)
    initiated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 2. API DESIGN

### 2.1 Pydantic Schemas

**File:** `models/jobs_management_schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class JobManagementStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    ARCHIVED = "archived"

class ExternalPortal(str, Enum):
    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    INDEED = "indeed"

class JobStatusUpdateRequest(BaseModel):
    status: JobManagementStatus
    reason: Optional[str] = None

class BulkUpdateRequest(BaseModel):
    job_ids: List[str] = Field(..., min_items=1, max_items=50)
    operation: str
    parameters: Dict[str, Any]
    dry_run: bool = False

class ExternalPostingRequest(BaseModel):
    portals: List[ExternalPortal]
    field_mappings: Optional[Dict[str, Dict[str, Any]]] = {}
    expires_in_days: int = 30

class DashboardResponse(BaseModel):
    success: bool = True
    jobs: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    summary: Dict[str, int]

class JobAnalyticsResponse(BaseModel):
    success: bool = True
    job_id: str
    date_range: Dict[str, date]
    funnel: Dict[str, int]
    conversion_rates: Dict[str, float]
    quality_metrics: Dict[str, Any]
    time_metrics: Dict[str, Any]
    trends: List[Dict[str, Any]]
```

### 2.2 API Endpoints

**File:** `api/jobs_management.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from models.jobs_management_schemas import *
from services.jobs_management_service import JobsManagementService
from core.dependencies import get_current_user
from core.database import get_db

router = APIRouter(prefix="/api/jobs-management", tags=["Jobs Management"])

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get jobs dashboard with filters"""
    service = JobsManagementService(db)
    return await service.get_dashboard(
        user_id=current_user["id"],
        status=status,
        department=department,
        search=search,
        page=page,
        limit=limit
    )

@router.put("/{job_id}/status")
async def update_job_status(
    job_id: str,
    status_data: JobStatusUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update job status"""
    service = JobsManagementService(db)
    return await service.update_job_status(
        job_id=job_id,
        new_status=status_data.status.value,
        reason=status_data.reason,
        user_id=current_user["id"]
    )

@router.get("/{job_id}/analytics", response_model=JobAnalyticsResponse)
async def get_job_analytics(
    job_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get job analytics"""
    from services.job_analytics_service import JobAnalyticsService
    service = JobAnalyticsService(db)
    return await service.get_job_analytics(job_id, date_from, date_to)

@router.post("/bulk-update", status_code=status.HTTP_202_ACCEPTED)
async def bulk_update_jobs(
    bulk_data: BulkUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Perform bulk operation"""
    from services.bulk_operations_service import BulkOperationsService
    service = BulkOperationsService(db)
    return await service.create_bulk_operation(
        job_ids=bulk_data.job_ids,
        operation_type=bulk_data.operation,
        parameters=bulk_data.parameters,
        initiated_by=current_user["id"]
    )

@router.post("/{job_id}/external-postings")
async def post_to_external_portals(
    job_id: str,
    posting_data: ExternalPostingRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Post job to external portals"""
    from services.external_posting_service import ExternalPostingService
    service = ExternalPostingService(db)
    return await service.post_to_portals(
        job_id=job_id,
        portals=[p.value for p in posting_data.portals],
        field_mappings=posting_data.field_mappings,
        user_id=current_user["id"]
    )

@router.get("/{job_id}/audit-log")
async def get_audit_log(
    job_id: str,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get audit log for job"""
    from services.audit_service import AuditService
    service = AuditService(db)
    return await service.get_audit_log(job_id, page, limit)
```

---

## 3. SERVICE LAYER

### 3.1 Jobs Management Service

**File:** `services/jobs_management_service.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, Dict, Any
from datetime import datetime
from models.database import Job, User, JobStatusHistory, generate_uuid

class JobsManagementService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_dashboard(self, user_id: str, status: Optional[str], 
                          department: Optional[str], search: Optional[str],
                          page: int, limit: int) -> Dict[str, Any]:
        """Get dashboard with filters"""
        query = select(Job).where(Job.deleted_at.is_(None))
        
        if status:
            query = query.where(Job.status == status)
        if department:
            query = query.where(Job.department == department)
        if search:
            query = query.where(or_(
                Job.title.ilike(f"%{search}%"),
                Job.department.ilike(f"%{search}%")
            ))
        
        # Get total count
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()
        
        # Paginate
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        jobs = result.scalars().all()
        
        # Get summary
        summary_query = select(Job.status, func.count()).where(Job.deleted_at.is_(None)).group_by(Job.status)
        summary_result = await self.db.execute(summary_query)
        summary = {"total_jobs": total, "open": 0, "closed": 0, "on_hold": 0, "archived": 0}
        for row in summary_result:
            summary[row[0]] = row[1]
        
        return {
            "success": True,
            "jobs": [self._format_job(j) for j in jobs],
            "pagination": {"total": total, "page": page, "limit": limit},
            "summary": summary
        }
    
    async def update_job_status(self, job_id: str, new_status: str, 
                               reason: Optional[str], user_id: str) -> Dict[str, Any]:
        """Update job status with validation"""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError("Job not found")
        
        old_status = job.status
        job.status = new_status
        if new_status == "closed":
            job.closed_at = datetime.utcnow()
        elif new_status == "archived":
            job.archived_at = datetime.utcnow()
        
        # Create history
        history = JobStatusHistory(
            id=generate_uuid(),
            job_id=job_id,
            from_status=old_status,
            to_status=new_status,
            reason=reason,
            changed_by=user_id
        )
        self.db.add(history)
        await self.db.commit()
        
        return {"success": True, "id": job_id, "status": new_status}
    
    def _format_job(self, job: Job) -> Dict[str, Any]:
        return {
            "id": job.id,
            "title": job.title,
            "department": job.department,
            "status": job.status,
            "posted_date": job.published_at,
            "view_count": job.view_count or 0
        }
```

### 3.2 Other Services (Stubs)

**File:** `services/job_analytics_service.py`
```python
class JobAnalyticsService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_job_analytics(self, job_id, date_from, date_to):
        # Calculate funnel, conversion rates, quality metrics
        return {
            "success": True,
            "job_id": job_id,
            "funnel": {"views": 100, "applications": 50},
            "conversion_rates": {"view_to_application": 50.0}
        }
```

**File:** `services/bulk_operations_service.py`
```python
class BulkOperationsService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def create_bulk_operation(self, job_ids, operation_type, parameters, initiated_by):
        # Create bulk operation record, process async
        return {"operation_id": "uuid", "status": "processing"}
```

**File:** `services/external_posting_service.py`
```python
class ExternalPostingService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def post_to_portals(self, job_id, portals, field_mappings, user_id):
        # Post to LinkedIn, Naukri, Indeed APIs
        return [{"portal": p, "status": "pending"} for p in portals]
```

**File:** `services/audit_service.py`
```python
import hashlib
import json

class AuditService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def log_status_change(self, job_id, old_status, new_status, user_id, ip_address):
        # Create audit log with checksum
        checksum = hashlib.sha256(f"{job_id}{new_status}{user_id}".encode()).hexdigest()
        # Insert into job_audit_log
        pass
    
    async def get_audit_log(self, job_id, page, limit):
        # Query audit log with pagination
        return {"success": True, "audit_entries": []}
```

---

## 4. UI/UX DESIGN

### 4.1 Dashboard Template

**File:** `templates/jobs_management/dashboard.html`

```html
{% extends "base.html" %}
{% block content %}
<div class="dashboard">
    <h1>Jobs Management</h1>
    
    <!-- Summary Cards -->
    <div class="summary-cards">
        <div class="card"><span>Total</span><strong id="total">0</strong></div>
        <div class="card"><span>Open</span><strong id="open">0</strong></div>
        <div class="card"><span>Closed</span><strong id="closed">0</strong></div>
    </div>
    
    <!-- Filters -->
    <div class="filters">
        <select id="status-filter"><option value="">All Status</option></select>
        <input type="text" id="search" placeholder="Search...">
    </div>
    
    <!-- Jobs Table -->
    <table id="jobs-table">
        <thead>
            <tr><th>Title</th><th>Status</th><th>Applications</th><th>Actions</th></tr>
        </thead>
        <tbody></tbody>
    </table>
</div>
<script src="/static/js/jobs_dashboard.js"></script>
{% endblock %}
```

### 4.2 JavaScript

**File:** `static/js/jobs_dashboard.js`

```javascript
async function loadDashboard() {
    const response = await fetch('/api/jobs-management/dashboard');
    const data = await response.json();
    
    // Update summary
    document.getElementById('total').textContent = data.summary.total_jobs;
    document.getElementById('open').textContent = data.summary.open;
    
    // Render table
    const tbody = document.querySelector('#jobs-table tbody');
    tbody.innerHTML = data.jobs.map(job => `
        <tr>
            <td>${job.title}</td>
            <td><span class="badge-${job.status}">${job.status}</span></td>
            <td>${job.application_count || 0}</td>
            <td>
                <button onclick="viewAnalytics('${job.id}')">Analytics</button>
                <button onclick="changeStatus('${job.id}')">Change Status</button>
            </td>
        </tr>
    `).join('');
}

async function changeStatus(jobId) {
    const newStatus = prompt('Enter new status:');
    await fetch(`/api/jobs-management/${jobId}/status`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({status: newStatus})
    });
    loadDashboard();
}

document.addEventListener('DOMContentLoaded', loadDashboard);
```

---

## 5. INTEGRATION POINTS

### 5.1 Existing Modules

**Authentication:** Use `get_current_user()` dependency from `core/dependencies.py`

**Job Service:** Modify `services/job_service.py`:
- Initialize `view_count=0` on job creation
- Create initial analytics record
- Add audit logging

**Application Service:** 
- Block applications to closed/archived jobs
- Update analytics on new application

**Notifications:** Send alerts on status changes via `services/notification_service.py`

### 5.2 New Dependencies

**Celery + Redis:**
```bash
pip install celery redis
```

**Configuration:**
```python
# .env
REDIS_URL=redis://localhost:6379/0
```

**Celery Tasks:** `services/scheduler_service.py`
```python
from celery import Celery
celery_app = Celery('jobs', broker='redis://localhost:6379/0')

@celery_app.task
def auto_close_expired_jobs():
    # Close jobs past deadline
    pass

@celery_app.task
def calculate_daily_analytics():
    # Update job_analytics table
    pass
```

---

## 6. FILE STRUCTURE

### New Files
```
├── migrations/008_create_jobs_management_tables.py
├── models/jobs_management_schemas.py
├── api/jobs_management.py
├── services/
│   ├── jobs_management_service.py
│   ├── job_analytics_service.py
│   ├── bulk_operations_service.py
│   ├── external_posting_service.py
│   ├── audit_service.py
│   └── scheduler_service.py
├── templates/jobs_management/
│   ├── dashboard.html
│   └── analytics.html
└── static/
    ├── js/jobs_dashboard.js
    └── css/jobs_management.css
```

### Modified Files
```
├── models/database.py (add ORM models)
├── main.py (register router)
├── services/job_service.py (add analytics init)
└── requirements.txt (add celery, redis)
```

---

## 7. TESTING STRATEGY

### Unit Tests
```python
# tests/test_jobs_management_service.py
async def test_update_job_status():
    service = JobsManagementService(db)
    result = await service.update_job_status(job_id, "closed", "Filled", user_id)
    assert result["status"] == "closed"

# tests/test_bulk_operations.py
async def test_bulk_status_update():
    service = BulkOperationsService(db)
    result = await service.create_bulk_operation(job_ids, "status_update", params, user_id)
    assert result["total_count"] == len(job_ids)
```

### Integration Tests
```python
# tests/integration/test_dashboard_api.py
async def test_dashboard_filters(client):
    response = await client.get("/api/jobs-management/dashboard?status=open")
    assert response.status_code == 200
    assert all(job["status"] == "open" for job in response.json()["jobs"])
```

---

## 8. DEPLOYMENT CONSIDERATIONS

### Environment Variables
```bash
REDIS_URL=redis://localhost:6379/0
LINKEDIN_CLIENT_ID=your_id
LINKEDIN_CLIENT_SECRET=your_secret
NAUKRI_API_KEY=your_key
INDEED_PUBLISHER_ID=your_id
```

### Migration
```bash
python migrations/008_create_jobs_management_tables.py
```

### Start Celery
```bash
celery -A services.scheduler_service worker -l info
celery -A services.scheduler_service beat -l info
```

### Register Router
```python
# main.py
from api.jobs_management import router as jobs_mgmt_router
app.include_router(jobs_mgmt_router)
```

---

**END OF DOCUMENT**
