"""API endpoints for Jobs Management feature"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import io
import csv
from datetime import datetime

from models.jobs_management_schemas import (
    JobStatusUpdateRequest, ExternalPostingRequest, BulkUpdateRequest,
    DashboardResponse, JobAnalyticsResponse, BulkOperationResponse,
    AuditLogResponse, StandardResponse, JobManagementStatus, ExternalPortal
)
from services.jobs_management_service import JobsManagementService
from services.job_analytics_service import JobAnalyticsService
from services.bulk_operations_service import BulkOperationsService
from services.external_posting_service import ExternalPostingService
from services.audit_service import AuditService
from core.dependencies import get_current_user
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs-management", tags=["Jobs Management"])


@router.get("/health")
async def health_check():
    """Health check endpoint for debugging"""
    return {"status": "ok", "message": "Jobs Management API is running"}


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    hiring_manager_id: Optional[str] = Query(None, description="Filter by hiring manager"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get jobs dashboard with filters, sorting, and pagination
    
    Returns paginated list of jobs with summary statistics
    """
    try:
        service = JobsManagementService(db)
        
        result = await service.get_dashboard(
            user_id=current_user["id"],
            user_role=current_user["role"],
            status=status,
            department=department,
            hiring_manager_id=hiring_manager_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get("/export")
async def export_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    hiring_manager_id: Optional[str] = Query(None, description="Filter by hiring manager"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export jobs to CSV with applied filters
    """
    try:
        service = JobsManagementService(db)
        
        # Get all jobs (no pagination for export)
        result = await service.get_dashboard(
            user_id=current_user["id"],
            user_role=current_user["role"],
            status=status,
            department=department,
            hiring_manager_id=hiring_manager_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort_by="created_at",
            sort_order="desc",
            page=1,
            limit=10000  # Get all jobs
        )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Job ID',
            'Title',
            'Department',
            'Status',
            'Posted Date',
            'Application Deadline',
            'Applications',
            'Avg Match Score',
            'Views',
            'Hiring Manager',
            'External Postings',
            'Last Updated'
        ])
        
        # Write data
        for job in result['jobs']:
            writer.writerow([
                job['uuid'],
                job['title'],
                job['department'] or '',
                job['status'],
                job['posted_date'].strftime('%Y-%m-%d') if job['posted_date'] else '',
                job['application_deadline'].strftime('%Y-%m-%d') if job['application_deadline'] else '',
                job['application_count'],
                f"{job['avg_match_score']:.1f}" if job['avg_match_score'] else '',
                job['view_count'],
                job['hiring_manager']['name'] if job['hiring_manager'] else '',
                ', '.join(job['external_postings']),
                job['last_updated'].strftime('%Y-%m-%d %H:%M:%S') if job['last_updated'] else ''
            ])
        
        # Return CSV as download
        output.seek(0)
        filename = f"jobs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Error exporting jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export jobs"
        )


# ============================================================================
# STATUS MANAGEMENT ENDPOINTS
# ============================================================================

@router.put("/{job_id}/status", response_model=StandardResponse)
async def update_job_status(
    job_id: str,
    status_data: JobStatusUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update job status with audit logging
    
    - **job_id**: Job UUID
    - **status**: New status (draft, open, on_hold, closed, archived)
    - **reason**: Optional reason for status change (required for closing)
    """
    try:
        service = JobsManagementService(db)
        audit_service = AuditService(db)
        
        # Update status
        updated_job = await service.update_job_status(
            job_id=job_id,
            new_status=status_data.status.value,
            reason=status_data.reason,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        # Create audit log
        await audit_service.log_status_change(
            job_id=job_id,
            old_status=updated_job.get("old_status"),
            new_status=status_data.status.value,
            reason=status_data.reason,
            user_id=current_user["id"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return StandardResponse(
            success=True,
            message="Job status updated successfully",
            data=updated_job
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job status"
        )


@router.delete("/{job_id}", response_model=StandardResponse)
async def soft_delete_job(
    job_id: str,
    permanent: bool = Query(False, description="Permanent deletion (admin only)"),
    request: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete (archive) or permanently delete a job
    
    - **job_id**: Job UUID
    - **permanent**: If true, permanently delete (requires admin role)
    
    Soft deletion archives the job for 90 days before permanent removal
    """
    try:
        # Check admin permission for permanent delete
        if permanent and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can permanently delete jobs"
            )
        
        service = JobsManagementService(db)
        audit_service = AuditService(db)
        
        result = await service.delete_job(
            job_id=job_id,
            permanent=permanent,
            user_id=current_user["id"]
        )
        
        # Create audit log
        await audit_service.log_deletion(
            job_id=job_id,
            permanent=permanent,
            user_id=current_user["id"],
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return StandardResponse(
            success=True,
            message=result["message"],
            data=result
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/{job_id}/analytics", response_model=JobAnalyticsResponse)
async def get_job_analytics(
    job_id: str,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive analytics for a job
    
    - **job_id**: Job UUID
    - **date_from**, **date_to**: Date range (default: last 30 days)
    
    Returns funnel metrics, conversion rates, quality metrics, and trends
    """
    try:
        service = JobAnalyticsService(db)
        
        analytics = await service.get_job_analytics(
            job_id=job_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return analytics
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job analytics"
        )


# ============================================================================
# BULK OPERATIONS ENDPOINTS
# ============================================================================

@router.post("/bulk-update", response_model=BulkOperationResponse, status_code=status.HTTP_202_ACCEPTED)
async def bulk_update_jobs(
    bulk_data: BulkUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform bulk operation on multiple jobs
    
    - **job_ids**: List of job UUIDs (max 50)
    - **operation**: Type of bulk operation (status_update, archive, etc.)
    - **parameters**: Operation-specific parameters
    - **dry_run**: If true, preview changes without applying
    
    Returns operation ID for status tracking
    """
    try:
        # Admin check for certain operations
        if bulk_data.operation.value == "archive" and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can perform bulk archive operations"
            )
        
        service = BulkOperationsService(db)
        
        operation = await service.create_bulk_operation(
            job_ids=bulk_data.job_ids,
            operation_type=bulk_data.operation.value,
            parameters=bulk_data.parameters,
            initiated_by=current_user["id"],
            dry_run=bulk_data.dry_run
        )
        
        # If not dry run, start processing (would be done in background)
        if not bulk_data.dry_run:
            # TODO: Trigger background task
            logger.info(f"Bulk operation {operation['operation_id']} queued for processing")
        
        return operation
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk operation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk operation"
        )


@router.get("/bulk-operations/{operation_id}", response_model=BulkOperationResponse)
async def get_bulk_operation_status(
    operation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of a bulk operation
    
    - **operation_id**: Bulk operation UUID
    
    Returns operation status, progress, and any errors
    """
    try:
        service = BulkOperationsService(db)
        
        operation = await service.get_operation_status(operation_id)
        
        return operation
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching bulk operation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bulk operation status"
        )


# ============================================================================
# EXTERNAL POSTING ENDPOINTS
# ============================================================================

@router.post("/{job_id}/external-postings", status_code=status.HTTP_202_ACCEPTED)
async def post_to_external_portals(
    job_id: str,
    posting_data: ExternalPostingRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Post job to external portals (LinkedIn, Naukri, Indeed)
    
    - **job_id**: Job UUID
    - **portals**: List of portals to post to
    - **field_mappings**: Portal-specific field mappings
    - **expires_in_days**: Posting expiration (default: 30 days)
    
    Returns posting status for each portal
    """
    try:
        service = ExternalPostingService(db)
        
        postings = await service.post_to_portals(
            job_id=job_id,
            portals=[p.value for p in posting_data.portals],
            field_mappings=posting_data.field_mappings,
            expires_in_days=posting_data.expires_in_days,
            user_id=current_user["id"]
        )
        
        return {
            "success": True,
            "message": "External posting initiated",
            "data": {"postings": postings}
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error posting to external portals: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to post to external portals"
        )


@router.get("/{job_id}/external-postings")
async def get_external_postings(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all external postings for a job
    
    - **job_id**: Job UUID
    
    Returns list of external postings with status
    """
    try:
        service = ExternalPostingService(db)
        
        postings = await service.get_job_postings(job_id)
        
        return {
            "success": True,
            "data": {"postings": postings}
        }
    
    except Exception as e:
        logger.error(f"Error fetching external postings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch external postings"
        )


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@router.get("/{job_id}/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    job_id: str,
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit log for a job
    
    - **job_id**: Job UUID
    - **action_type**: Filter by action type
    - **user_id**: Filter by user
    - **date_from**, **date_to**: Date range filter
    
    Returns chronological audit trail with pagination
    """
    try:
        service = AuditService(db)
        
        audit_log = await service.get_audit_log(
            job_id=job_id,
            action_type=action_type,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit
        )
        
        return audit_log
    
    except Exception as e:
        logger.error(f"Error fetching audit log: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch audit log"
        )


@router.get("/audit-log/export/{job_id}")
async def export_audit_log(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export audit log as CSV
    
    - **job_id**: Job UUID
    
    Returns CSV file download
    """
    try:
        service = AuditService(db)
        
        csv_data = await service.export_audit_log_csv(job_id)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_log_{job_id}.csv"}
        )
    
    except Exception as e:
        logger.error(f"Error exporting audit log: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit log"
        )


# ============================================================================
# STATUS HISTORY ENDPOINT
# ============================================================================

@router.get("/{job_id}/status-history")
async def get_status_history(
    job_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of entries"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status change history for a job
    
    - **job_id**: Job UUID
    - **limit**: Maximum number of entries (default: 10)
    
    Returns chronological list of status changes
    """
    try:
        service = JobsManagementService(db)
        
        history = await service.get_job_status_history(job_id, limit)
        
        return {
            "success": True,
            "data": {"history": history}
        }
    
    except Exception as e:
        logger.error(f"Error fetching status history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch status history"
        )
