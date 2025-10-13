"""Client management API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date

from core.database import get_db
from models.client_schemas import (
    ClientCreateRequest, ClientUpdateRequest, ClientDeactivateRequest,
    ClientResponse, ClientDetailResponse, ClientListResponse,
    ClientDashboardResponse, CommunicationCreateRequest,
    CommunicationListResponse, FeedbackCreateRequest,
    FeedbackListResponse, ClientJobListResponse,
    ClientContactCreate, BulkClientOperationRequest,
    BulkClientOperationResponse
)
from services.client_management_service import ClientManagementService
from services.client_communication_service import ClientCommunicationService
from services.client_feedback_service import ClientFeedbackService
from services.client_analytics_service import ClientAnalyticsService
from models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["Client Management"])


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


# Client CRUD Endpoints

@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreateRequest,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a new client (Admin, Manager only)
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        # For testing, create a mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found. Please create a user first.")
        
        service = ClientManagementService(db)
        client = await service.create_client(data, current_user)
        
        # Load account manager
        if client.account_manager_id:
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.id == client.account_manager_id))
            manager = result.scalar_one_or_none()
            client.account_manager = manager
        
        return client
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    industry: Optional[str] = None,
    account_manager_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(get_current_user)
):
    """List all clients with pagination and filters
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        service = ClientManagementService(db)
        result = await service.list_clients(
            status=status,
            industry=industry,
            account_manager_id=account_manager_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error listing clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(get_current_user)
):
    """Get client details
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        service = ClientManagementService(db)
        client = await service.get_client_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Load contacts
        contacts = await service.get_client_contacts(client_id)
        
        # Load account manager
        if client.account_manager_id:
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.id == client.account_manager_id))
            manager = result.scalar_one_or_none()
            client.account_manager = manager
        
        # Get stats
        analytics_service = ClientAnalyticsService(db)
        stats = await analytics_service._get_client_stats(client_id)
        
        return {
            **client.__dict__,
            "contacts": contacts,
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    data: ClientUpdateRequest,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Update client information
    
    TEMPORARY: Authentication disabled for initial testing
    """
    # Mock user for testing
    from sqlalchemy import select
    result = await db.execute(select(User).limit(1))
    current_user = result.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=500, detail="No users found")
    try:
        service = ClientManagementService(db)
        client = await service.update_client(client_id, data, current_user)
        
        # Load account manager
        if client.account_manager_id:
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.id == client.account_manager_id))
            manager = result.scalar_one_or_none()
            client.account_manager = manager
        
        return client
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{client_id}/deactivate", response_model=ClientResponse)
async def deactivate_client(
    client_id: str,
    data: ClientDeactivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Deactivate a client (Admin only)"""
    try:
        service = ClientManagementService(db)
        client = await service.deactivate_client(client_id, data, current_user)
        return client
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{client_id}/reactivate", response_model=ClientResponse)
async def reactivate_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Reactivate a deactivated client (Admin only)"""
    try:
        service = ClientManagementService(db)
        client = await service.reactivate_client(client_id, current_user)
        return client
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard Endpoint

@router.get("/{client_id}/dashboard", response_model=ClientDashboardResponse)
async def get_client_dashboard(
    client_id: str,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(get_current_user)
):
    """Get client dashboard with stats and activities
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        # Get client details
        service = ClientManagementService(db)
        client = await service.get_client_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get dashboard data
        analytics_service = ClientAnalyticsService(db)
        dashboard_data = await analytics_service.get_dashboard_data(client_id)
        
        # Load contacts
        contacts = await service.get_client_contacts(client_id)
        
        return {
            "client": {**client.__dict__, "contacts": contacts, "stats": {}},
            **dashboard_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Communication Endpoints

@router.post("/{client_id}/communications", status_code=status.HTTP_201_CREATED)
async def log_communication(
    client_id: str,
    data: CommunicationCreateRequest,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(get_current_user)
):
    """Log a communication with the client
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found")
        
        service = ClientCommunicationService(db)
        communication = await service.log_communication(client_id, data, current_user)
        return communication
    except Exception as e:
        logger.error(f"Error logging communication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{client_id}/contacts", status_code=status.HTTP_201_CREATED)
async def add_contact(
    client_id: str,
    data: ClientContactCreate,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(get_current_user)
):
    """Add a contact to a client
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        service = ClientManagementService(db)
        contact = await service.add_contact(client_id, data)
        return contact
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Feedback Endpoints

@router.post("/{client_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    client_id: str,
    data: FeedbackCreateRequest,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Submit feedback for a client (Admin, Manager only)
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        current_user = result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=500, detail="No users found")
        
        service = ClientFeedbackService(db)
        feedback = await service.submit_feedback(client_id, data, current_user)
        return feedback
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Job Linking Endpoints

@router.post("/{client_id}/jobs/{job_id}", status_code=status.HTTP_201_CREATED)
async def link_job_to_client(
    client_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db)
    # TEMPORARILY DISABLED: current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Link a job to a client (Admin, Manager only)
    
    TEMPORARY: Authentication disabled for initial testing
    """
    try:
        from models.database import Client, Job, ClientJobAssignment
        from sqlalchemy import select
        
        # Check client exists
        client_result = await db.execute(select(Client).where(Client.id == client_id))
        client = client_result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check job exists
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if already linked
        existing = await db.execute(
            select(ClientJobAssignment).where(
                ClientJobAssignment.client_id == client_id,
                ClientJobAssignment.job_id == job_id,
                ClientJobAssignment.is_active == True
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Job already linked to this client")
        
        # Create assignment
        assignment = ClientJobAssignment(
            client_id=client_id,
            job_id=job_id,
            is_active=True
        )
        db.add(assignment)
        await db.commit()
        
        return {"message": "Job linked successfully", "client_id": client_id, "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error linking job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
