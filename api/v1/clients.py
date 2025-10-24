"""Client Management API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.database import get_db
from core.auth import get_current_user
from models.database import Client, User, Job
from models.client_schemas import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse,
    ClientFilter
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("", response_model=Dict[str, Any])
async def list_clients(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """List all clients with pagination, search, and filtering"""
    try:
        # Build query
        query = select(Client).where(Client.is_deleted == False)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Client.company_name.ilike(search_term),
                    Client.contact_person.ilike(search_term),
                    Client.contact_email.ilike(search_term)
                )
            )
        
        # Apply status filter
        if status:
            query = query.where(Client.status == status)
        
        # Apply type filter
        if type:
            query = query.where(Client.client_type == type)
        
        # Get total count
        count_query = select(func.count(Client.id)).where(Client.is_deleted == False)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                or_(
                    Client.company_name.ilike(search_term),
                    Client.contact_person.ilike(search_term),
                    Client.contact_email.ilike(search_term)
                )
            )
        if status:
            count_query = count_query.where(Client.status == status)
        if type:
            count_query = count_query.where(Client.client_type == type)
        
        result = await db.execute(count_query)
        total = result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Client.created_at.desc()).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        # Format response
        clients_data = []
        for client in clients:
            clients_data.append({
                "id": client.id,
                "company_name": client.company_name,
                "contact_person": client.contact_person,
                "contact_email": client.contact_email,
                "contact_phone": client.contact_phone,
                "industry": client.industry,
                "status": client.status,
                "client_type": client.client_type,
                "priority": client.priority,
                "created_at": client.created_at.isoformat() if client.created_at else None,
                "updated_at": client.updated_at.isoformat() if client.updated_at else None,
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "results": clients_data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
    
    except Exception as e:
        logger.error(f"Error listing clients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list clients")


@router.post("", response_model=Dict[str, Any])
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new client"""
    try:
        # Check if company already exists
        existing = await db.execute(
            select(Client).where(Client.company_name == client_data.company_name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Client with this company name already exists")
        
        # Create new client
        new_client = Client(
            company_name=client_data.company_name,
            industry=client_data.industry,
            website=client_data.website,
            description=client_data.description,
            contact_person=client_data.contact_person,
            contact_email=client_data.contact_email,
            contact_phone=client_data.contact_phone,
            address=client_data.address,
            city=client_data.city,
            state=client_data.state,
            country=client_data.country,
            postal_code=client_data.postal_code,
            status="active",
            client_type=client_data.client_type or "direct",
            priority=client_data.priority or "medium",
            notes=client_data.notes,
            created_by=current_user.id
        )
        
        db.add(new_client)
        await db.commit()
        await db.refresh(new_client)
        
        return {
            "success": True,
            "message": "Client created successfully",
            "client_id": new_client.id,
            "data": {
                "id": new_client.id,
                "company_name": new_client.company_name,
                "contact_email": new_client.contact_email,
                "status": new_client.status,
                "created_at": new_client.created_at.isoformat() if new_client.created_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create client")


@router.get("/{client_id}", response_model=Dict[str, Any])
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get client details"""
    try:
        result = await db.execute(
            select(Client).where(
                and_(Client.id == client_id, Client.is_deleted == False)
            )
        )
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get job count
        jobs_result = await db.execute(
            select(func.count(Job.id)).where(Job.client_id == client_id)
        )
        jobs_count = jobs_result.scalar() or 0
        
        return {
            "id": client.id,
            "company_name": client.company_name,
            "industry": client.industry,
            "website": client.website,
            "description": client.description,
            "contact_person": client.contact_person,
            "contact_email": client.contact_email,
            "contact_phone": client.contact_phone,
            "address": client.address,
            "city": client.city,
            "state": client.state,
            "country": client.country,
            "postal_code": client.postal_code,
            "status": client.status,
            "client_type": client.client_type,
            "priority": client.priority,
            "contract_start_date": client.contract_start_date.isoformat() if client.contract_start_date else None,
            "contract_end_date": client.contract_end_date.isoformat() if client.contract_end_date else None,
            "contract_value": client.contract_value,
            "payment_terms": client.payment_terms,
            "notes": client.notes,
            "jobs_count": jobs_count,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get client")


@router.put("/{client_id}", response_model=Dict[str, Any])
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update client details"""
    try:
        result = await db.execute(
            select(Client).where(
                and_(Client.id == client_id, Client.is_deleted == False)
            )
        )
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Update fields
        update_data = client_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(client, field, value)
        
        client.updated_by = current_user.id
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        return {
            "success": True,
            "message": "Client updated successfully",
            "data": {
                "id": client.id,
                "company_name": client.company_name,
                "status": client.status,
                "updated_at": client.updated_at.isoformat() if client.updated_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update client")


@router.delete("/{client_id}", response_model=Dict[str, Any])
async def delete_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Soft delete a client"""
    try:
        result = await db.execute(
            select(Client).where(
                and_(Client.id == client_id, Client.is_deleted == False)
            )
        )
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Soft delete
        client.is_deleted = True
        client.deleted_at = datetime.utcnow()
        client.deleted_by = current_user.id
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Client deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete client")


@router.get("/{client_id}/jobs", response_model=Dict[str, Any])
async def get_client_jobs(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all jobs for a client"""
    try:
        # Verify client exists
        client_result = await db.execute(
            select(Client).where(
                and_(Client.id == client_id, Client.is_deleted == False)
            )
        )
        client = client_result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get jobs
        jobs_result = await db.execute(
            select(Job).where(Job.client_id == client_id).order_by(Job.created_at.desc())
        )
        jobs = jobs_result.scalars().all()
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                "id": job.id,
                "title": job.title,
                "status": job.status,
                "location_city": job.location_city,
                "created_at": job.created_at.isoformat() if job.created_at else None,
            })
        
        return {
            "client_id": client_id,
            "company_name": client.company_name,
            "jobs": jobs_data,
            "total_jobs": len(jobs_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get client jobs")
