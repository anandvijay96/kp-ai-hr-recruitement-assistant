"""Client Management API Endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database import get_db
from models.client_schemas import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse, ClientFilter,
    ClientContactCreate, ClientContactUpdate, ClientContactResponse,
    ClientJobCreate, ClientJobUpdate, ClientJobResponse,
    ClientActivityCreate, ClientActivityUpdate, ClientActivityResponse,
    ClientDeactivateRequest
)
from services.client_service import ClientService
from models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["Client Management"])


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Get current authenticated user from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


# ============================================================================
# CLIENT CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new client"""
    try:
        service = ClientService(db)
        client = await service.create_client(client_data, current_user.id)
        
        # Format response
        return ClientResponse(
            **client.__dict__,
            contacts_count=0,
            jobs_count=0,
            active_jobs_count=0
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ClientListResponse)
async def get_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search_query: Optional[str] = None,
    status: Optional[str] = None,
    industry: Optional[str] = None,
    city: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|company_name|status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all clients with filtering and pagination"""
    try:
        service = ClientService(db)
        
        # Build filters
        filters = ClientFilter(
            search_query=search_query,
            status=[status] if status else None,
            industry=industry,
            city=city,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = await service.search_clients(filters, page, page_size)
        
        # Format response
        clients = [ClientResponse(**client) for client in result['clients']]
        
        return ClientListResponse(
            clients=clients,
            total=result['total'],
            page=result['page'],
            page_size=result['page_size'],
            total_pages=result['total_pages']
        )
    except Exception as e:
        logger.error(f"Error getting clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get client by ID"""
    try:
        service = ClientService(db)
        client = await service.get_client(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get counts
        contacts_count = len(client.contacts) if hasattr(client, 'contacts') else 0
        jobs_count = len(client.jobs) if hasattr(client, 'jobs') else 0
        active_jobs_count = sum(1 for job in client.jobs if job.status == 'open') if hasattr(client, 'jobs') else 0
        
        return ClientResponse(
            **client.__dict__,
            contacts_count=contacts_count,
            jobs_count=jobs_count,
            active_jobs_count=active_jobs_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update client"""
    try:
        service = ClientService(db)
        client = await service.update_client(client_id, client_data)
        
        # Get counts
        contacts_count = len(client.contacts) if hasattr(client, 'contacts') else 0
        jobs_count = len(client.jobs) if hasattr(client, 'jobs') else 0
        active_jobs_count = sum(1 for job in client.jobs if job.status == 'open') if hasattr(client, 'jobs') else 0
        
        return ClientResponse(
            **client.__dict__,
            contacts_count=contacts_count,
            jobs_count=jobs_count,
            active_jobs_count=active_jobs_count
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (deactivate) client"""
    try:
        service = ClientService(db)
        await service.delete_client(client_id)
        
        return {"success": True, "message": "Client deactivated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CLIENT CONTACT ENDPOINTS
# ============================================================================

@router.post("/{client_id}/contacts", response_model=ClientContactResponse)
async def create_contact(
    client_id: str,
    contact_data: ClientContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new contact for a client"""
    try:
        # Ensure client_id matches
        contact_data.client_id = client_id
        
        service = ClientService(db)
        contact = await service.create_contact(contact_data, current_user.id)
        
        return ClientContactResponse(**contact.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}/contacts", response_model=List[ClientContactResponse])
async def get_client_contacts(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all contacts for a client"""
    try:
        service = ClientService(db)
        contacts = await service.get_client_contacts(client_id)
        
        return [ClientContactResponse(**contact.__dict__) for contact in contacts]
    except Exception as e:
        logger.error(f"Error getting contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/contacts/{contact_id}", response_model=ClientContactResponse)
async def update_contact(
    contact_id: str,
    contact_data: ClientContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a client contact"""
    try:
        service = ClientService(db)
        contact = await service.update_contact(contact_id, contact_data)
        
        return ClientContactResponse(**contact.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CLIENT JOB ENDPOINTS
# ============================================================================

@router.post("/{client_id}/jobs", response_model=ClientJobResponse)
async def create_job(
    client_id: str,
    job_data: ClientJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job for a client"""
    try:
        # Ensure client_id matches
        job_data.client_id = client_id
        
        service = ClientService(db)
        job = await service.create_job(job_data, current_user.id)
        
        return ClientJobResponse(**job.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}/jobs", response_model=List[ClientJobResponse])
async def get_client_jobs(
    client_id: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all jobs for a client"""
    try:
        service = ClientService(db)
        jobs = await service.get_client_jobs(client_id, status)
        
        return [ClientJobResponse(**job.__dict__) for job in jobs]
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CLIENT ACTIVITY ENDPOINTS
# ============================================================================

@router.post("/{client_id}/activities", response_model=ClientActivityResponse)
async def create_activity(
    client_id: str,
    activity_data: ClientActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activity for a client"""
    try:
        # Ensure client_id matches
        activity_data.client_id = client_id
        
        service = ClientService(db)
        activity = await service.create_activity(activity_data, current_user.id)
        
        return ClientActivityResponse(**activity.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}/activities", response_model=List[ClientActivityResponse])
async def get_client_activities(
    client_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activities for a client"""
    try:
        service = ClientService(db)
        activities = await service.get_client_activities(client_id, limit)
        
        return [ClientActivityResponse(**activity.__dict__) for activity in activities]
    except Exception as e:
        logger.error(f"Error getting activities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@router.get("/stats/overview")
async def get_client_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall client statistics"""
    try:
        service = ClientService(db)
        stats = await service.get_client_statistics()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
