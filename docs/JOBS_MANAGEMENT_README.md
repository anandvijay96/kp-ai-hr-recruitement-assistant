# Jobs Management Feature - Implementation Guide

## Overview
Feature 8: Jobs Management provides comprehensive job lifecycle management with analytics, bulk operations, external portal integration, and audit trails.

## Installation & Setup

### 1. Run Database Migration
```bash
python migrations/008_create_jobs_management_tables.py
```

### 2. Verify Database Tables
The migration creates:
- `job_analytics` - Daily aggregated metrics
- `job_external_postings` - External portal postings
- `job_audit_log` - Immutable audit trail
- `bulk_operations` - Bulk operation tracking

And modifies:
- `jobs` table - Adds `archived_at`, `view_count`, `application_deadline`
- `job_status_history` table - Adds `reason` column

### 3. Access the Dashboard
Navigate to: `http://localhost:8000/jobs-management/dashboard`

## Features Implemented

### ✅ Dashboard
- **URL**: `/jobs-management/dashboard`
- **Features**:
  - Summary cards (Total, Open, Closed, On Hold, Archived)
  - Advanced filters (status, department, date range, search)
  - Sortable columns
  - Pagination (20 jobs per page)
  - Bulk selection
  - Export functionality

### ✅ Status Management
- **Valid Transitions**:
  - draft → open
  - open → on_hold, closed
  - on_hold → open, closed
  - closed → archived
- **Features**:
  - Status change with reason
  - Automatic timestamps
  - Status history tracking
  - Audit logging

### ✅ Job Analytics
- **URL**: `/jobs-management/{job_id}/analytics`
- **Metrics**:
  - Funnel metrics (views → applications → hires)
  - Conversion rates
  - Time metrics (time-to-fill, time-to-first-application)
  - Match score distribution
  - Trends over time

### ✅ Bulk Operations
- **Operations**:
  - Status update (max 50 jobs)
  - Archive jobs
  - Update deadline
- **Features**:
  - Preview before execution
  - Progress tracking
  - Error handling with detailed reports
  - Dry-run mode

### ✅ External Posting
- **Portals**: LinkedIn, Naukri, Indeed
- **Features**:
  - Multi-portal posting
  - Field mapping per portal
  - Status tracking (pending, posted, failed)
  - Retry logic
  - Expiration management

### ✅ Audit Trail
- **URL**: `/jobs-management/{job_id}/audit-log`
- **Features**:
  - Immutable log entries
  - Tamper detection (SHA-256 checksums)
  - Filterable by action type, user, date
  - CSV export
  - 7-year retention

## API Endpoints

### Dashboard
```http
GET /api/jobs-management/dashboard
  ?status=open
  &department=Engineering
  &search=software
  &page=1
  &limit=20
```

### Status Management
```http
PUT /api/jobs-management/{job_id}/status
Content-Type: application/json

{
  "status": "closed",
  "reason": "Position filled"
}
```

### Analytics
```http
GET /api/jobs-management/{job_id}/analytics
  ?date_from=2025-09-01
  &date_to=2025-10-08
```

### Bulk Operations
```http
POST /api/jobs-management/bulk-update
Content-Type: application/json

{
  "job_ids": ["uuid1", "uuid2"],
  "operation": "status_update",
  "parameters": {
    "status": "on_hold",
    "reason": "Budget review"
  }
}
```

### External Posting
```http
POST /api/jobs-management/{job_id}/external-postings
Content-Type: application/json

{
  "portals": ["linkedin", "naukri"],
  "field_mappings": {
    "linkedin": {
      "job_function": "Engineering"
    }
  },
  "expires_in_days": 30
}
```

### Audit Log
```http
GET /api/jobs-management/{job_id}/audit-log
  ?action_type=status_change
  &page=1
  &limit=20
```

## Testing

### Run Unit Tests
```bash
pytest tests/test_jobs_management_service.py -v
```

### Run All Tests
```bash
pytest tests/ -v --cov=services --cov=api
```

### Manual Testing Checklist

#### Dashboard
- [ ] Load dashboard with multiple jobs
- [ ] Apply status filter
- [ ] Apply department filter
- [ ] Search by job title
- [ ] Sort by different columns
- [ ] Navigate pagination
- [ ] Select multiple jobs
- [ ] Export to CSV

#### Status Management
- [ ] Change job from open to on_hold
- [ ] Try invalid transition (should fail)
- [ ] Close job with reason
- [ ] Archive closed job (admin only)
- [ ] View status history

#### Analytics
- [ ] View analytics for job with applications
- [ ] Change date range
- [ ] Verify funnel metrics
- [ ] Check conversion rates
- [ ] View trends chart

#### Bulk Operations
- [ ] Select 5 jobs
- [ ] Bulk update status
- [ ] Verify all jobs updated
- [ ] Check audit log for each job
- [ ] Try bulk operation with > 50 jobs (should fail)

#### External Posting
- [ ] Post job to LinkedIn
- [ ] Post to multiple portals
- [ ] View posting status
- [ ] Handle posting failure

#### Audit Log
- [ ] View audit log for job
- [ ] Filter by action type
- [ ] Filter by user
- [ ] Export to CSV
- [ ] Verify checksum integrity

## Permissions

### Role-Based Access
- **Admin**: Full access including archive and permanent delete
- **Manager**: Create, update, view analytics
- **Recruiter**: View dashboard, view analytics (read-only)

### Endpoint Permissions
- `PUT /status` - All authenticated users
- `DELETE /{job_id}?permanent=true` - Admin only
- `POST /bulk-update` (archive operation) - Admin only
- `GET /dashboard` - All authenticated users
- `GET /analytics` - All authenticated users
- `GET /audit-log` - All authenticated users

## Configuration

### Environment Variables
```bash
# Optional: External portal API keys
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_secret
NAUKRI_API_KEY=your_api_key
INDEED_PUBLISHER_ID=your_publisher_id
```

### Status Transition Rules
Configured in `JobsManagementService.VALID_TRANSITIONS`:
```python
VALID_TRANSITIONS = {
    "draft": ["open"],
    "open": ["on_hold", "closed"],
    "on_hold": ["open", "closed"],
    "closed": ["archived"],
    "archived": []
}
```

## Troubleshooting

### Migration Fails
```bash
# Check database connection
python -c "from core.database import engine; import asyncio; asyncio.run(engine.connect())"

# Rollback migration
python migrations/008_create_jobs_management_tables.py downgrade
```

### Dashboard Not Loading
1. Check browser console for errors
2. Verify auth token is valid
3. Check API endpoint: `GET /api/jobs-management/dashboard`
4. Verify database tables exist

### Status Update Fails
- Check valid transitions in `JobsManagementService`
- Verify user has required permissions
- Check if reason is provided for closing

### Analytics Not Showing Data
- Analytics are calculated daily (placeholder data initially)
- Run manual analytics update if needed
- Check `job_analytics` table for data

## Future Enhancements

### Planned Features
1. **Automated Rules**
   - Auto-close jobs after deadline
   - Auto-archive jobs 90 days after closure
   - Scheduled Celery tasks

2. **Real-time Updates**
   - WebSocket support for live dashboard updates
   - Real-time application count updates

3. **Advanced Analytics**
   - Predictive analytics (time-to-fill estimation)
   - Comparison with industry benchmarks
   - Recruiter performance metrics

4. **External Portal Integration**
   - Complete LinkedIn API integration
   - Naukri API integration
   - Indeed API integration
   - Application sync from portals

5. **Notifications**
   - Email notifications on status changes
   - Slack/Teams integration
   - Mobile push notifications

## Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Review API documentation: `/docs`
3. Run diagnostics: `python verify_implementation.py`

## License
Internal use only - HR Recruitment Application
