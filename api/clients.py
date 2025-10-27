"""Client Management API Endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database import get_db
from models.client_schemas import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse, ClientFilter
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
    """Delete (soft delete) client"""
    try:
        service = ClientService(db)
        await service.delete_client(client_id, current_user.id)
        
        return {"success": True, "message": "Client deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: Endpoints for client_contacts, client_jobs, and client_activities tables
# are not implemented because those tables don't exist in the current schema.
# Only the main 'clients' table was created by the migration.
# To enable these features, run the add_client_management_tables.py migration.
