"""Client Management Service"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from models.client_models import Client  # Only import Client, other classes don't exist yet
from models.client_schemas import (
    ClientCreate, ClientUpdate, ClientFilter
)

logger = logging.getLogger(__name__)


class ClientService:
    """Service for managing clients"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============================================================================
    # CLIENT CRUD OPERATIONS
    # ============================================================================
    
    async def create_client(self, client_data: ClientCreate, created_by: str) -> Client:
        """Create a new client"""
        try:
            # Check if client with same name already exists
            existing = await self.db.execute(
                select(Client).where(Client.company_name == client_data.company_name)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Client with name {client_data.company_name} already exists")
            
            # Create client
            client = Client(
                **client_data.model_dump(),
                created_by=created_by,
                status="active"
            )
            
            self.db.add(client)
            await self.db.commit()
            await self.db.refresh(client)
            
            logger.info(f"Created client: {client.company_name} (ID: {client.id})")
            return client
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating client: {str(e)}")
            raise
    
    async def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID with relationships"""
        try:
            result = await self.db.execute(
                select(Client)
                .where(Client.id == client_id)
                .where(Client.is_deleted == False)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting client: {str(e)}")
            raise
    
    async def update_client(self, client_id: str, client_data: ClientUpdate) -> Client:
        """Update client"""
        try:
            client = await self.get_client(client_id)
            if not client:
                raise ValueError(f"Client not found: {client_id}")
            
            # Update fields
            update_data = client_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(client, field, value)
            
            await self.db.commit()
            await self.db.refresh(client)
            
            logger.info(f"Updated client: {client.company_name} (ID: {client_id})")
            return client
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating client: {str(e)}")
            raise
    
    async def delete_client(self, client_id: str, deleted_by: str) -> bool:
        """Delete client (soft delete)"""
        try:
            client = await self.get_client(client_id)
            if not client:
                raise ValueError(f"Client not found: {client_id}")
            
            client.is_deleted = True
            client.deleted_at = datetime.utcnow()
            client.deleted_by = deleted_by
            
            await self.db.commit()
            
            logger.info(f"Deleted client: {client.company_name} (ID: {client_id})")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting client: {str(e)}")
            raise
    
    async def search_clients(
        self,
        filters: ClientFilter,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search and filter clients"""
        try:
            # Build base query
            query = select(Client)
            filter_conditions = []
            
            # Search query (company name, email, city, industry)
            if filters.search_query:
                search_term = f"%{filters.search_query}%"
                filter_conditions.append(
                    or_(
                        Client.company_name.ilike(search_term),
                        Client.contact_email.ilike(search_term),
                        Client.contact_person.ilike(search_term),
                        Client.city.ilike(search_term),
                        Client.industry.ilike(search_term)
                    )
                )
            
            # Status filter
            if filters.status:
                filter_conditions.append(Client.status.in_(filters.status))
            
            # Industry filter
            if filters.industry:
                filter_conditions.append(Client.industry.ilike(f"%{filters.industry}%"))
            
            # Client type filter
            if hasattr(filters, 'client_type') and filters.client_type:
                filter_conditions.append(Client.client_type.in_(filters.client_type))
            
            # City filter
            if filters.city:
                filter_conditions.append(Client.city.ilike(f"%{filters.city}%"))
            
            # Country filter
            if filters.country:
                filter_conditions.append(Client.country.ilike(f"%{filters.country}%"))
            
            # Apply filters
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
            
            # Get total count
            count_query = select(func.count(Client.id)).select_from(Client)
            if filter_conditions:
                count_query = count_query.filter(and_(*filter_conditions))
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar() or 0
            
            # Apply sorting
            sort_column_map = {
                'created_at': Client.created_at,
                'updated_at': Client.updated_at,
                'company_name': Client.company_name,
                'status': Client.status
            }
            sort_column = sort_column_map.get(filters.sort_by, Client.created_at)
            
            if filters.sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            clients = result.scalars().all()
            
            # Format results
            client_list = []
            for client in clients:
                client_dict = {
                    **client.__dict__,
                    'contacts_count': 0,
                    'jobs_count': 0,
                    'active_jobs_count': 0
                }
                client_list.append(client_dict)
            
            return {
                "clients": client_list,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"Error searching clients: {str(e)}")
            raise
    
    # NOTE: Methods for client_contacts, client_jobs, and client_activities tables
    # are not implemented because those tables don't exist in the current schema.
    # Only the main 'clients' table was created by the migration.
    # To enable these features, run the add_client_management_tables.py migration.
