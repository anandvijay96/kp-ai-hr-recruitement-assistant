"""
Reports API - Phase 3 Day 7
============================
API endpoints for generating and exporting reports.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from core.database import get_db
from core.auth import get_current_user
from models.database import User
from services.activity_tracker import ActivityTracker
from services.report_generator import ReportGenerator
from services.interview_scheduler import InterviewScheduler
from services.candidate_workflow import CandidateWorkflowService

router = APIRouter()


@router.get("/reports/activity")
async def generate_activity_report(
    days: int = 30,
    format: str = 'json',
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate activity report for specified period.
    
    Formats: json, csv, pdf, excel
    """
    # Check permissions
    if user_id and user_id != current_user.id and current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    target_user_id = user_id or current_user.id
    
    # Get activity data
    tracker = ActivityTracker(db)
    summary = await tracker.get_user_activity_summary(target_user_id, days=days)
    
    # Generate report
    generator = ReportGenerator()
    report_data = generator.generate_activity_report(summary, format=format)
    
    # Set content type based on format
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    filename_extensions = {
        'json': 'json',
        'csv': 'csv',
        'pdf': 'pdf',
        'excel': 'xlsx'
    }
    
    filename = f"activity_report_{datetime.now().strftime('%Y%m%d')}.{filename_extensions.get(format, 'txt')}"
    
    return Response(
        content=report_data,
        media_type=content_types.get(format, 'text/plain'),
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@router.get("/reports/team-performance")
async def generate_team_performance_report(
    period: str = 'month',
    format: str = 'json',
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate team performance report (admin only).
    """
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tracker = ActivityTracker(db)
    leaderboard = await tracker.get_team_leaderboard(period=period, limit=50)
    
    report_data = {
        'period': period,
        'generated_at': datetime.now().isoformat(),
        'team_performance': leaderboard
    }
    
    generator = ReportGenerator()
    report_bytes = generator.generate_activity_report(report_data, format=format)
    
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    extensions = {'json': 'json', 'csv': 'csv', 'pdf': 'pdf', 'excel': 'xlsx'}
    filename = f"team_performance_{period}_{datetime.now().strftime('%Y%m%d')}.{extensions.get(format, 'txt')}"
    
    return Response(
        content=report_bytes,
        media_type=content_types.get(format, 'text/plain'),
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@router.get("/reports/interviews")
async def generate_interview_report(
    format: str = 'json',
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate interview statistics report."""
    scheduler = InterviewScheduler(db)
    stats = await scheduler.get_interview_statistics()
    
    report_data = {
        'generated_at': datetime.now().isoformat(),
        'interview_statistics': stats
    }
    
    generator = ReportGenerator()
    report_bytes = generator.generate_activity_report(report_data, format=format)
    
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    extensions = {'json': 'json', 'csv': 'csv', 'pdf': 'pdf', 'excel': 'xlsx'}
    filename = f"interview_report_{datetime.now().strftime('%Y%m%d')}.{extensions.get(format, 'txt')}"
    
    return Response(
        content=report_bytes,
        media_type=content_types.get(format, 'text/plain'),
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@router.get("/reports/workflow")
async def generate_workflow_report(
    format: str = 'json',
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate candidate workflow statistics report."""
    workflow = CandidateWorkflowService(db)
    stats = await workflow.get_workflow_statistics()
    
    report_data = {
        'generated_at': datetime.now().isoformat(),
        'workflow_statistics': stats
    }
    
    generator = ReportGenerator()
    report_bytes = generator.generate_activity_report(report_data, format=format)
    
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    extensions = {'json': 'json', 'csv': 'csv', 'pdf': 'pdf', 'excel': 'xlsx'}
    filename = f"workflow_report_{datetime.now().strftime('%Y%m%d')}.{extensions.get(format, 'txt')}"
    
    return Response(
        content=report_bytes,
        media_type=content_types.get(format, 'text/plain'),
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
