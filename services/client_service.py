"""Client Management Service"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from models.client_models import Client, ClientContact, ClientJob, ClientActivity
from models.client_schemas import (
    ClientCreate, ClientUpdate, ClientFilter,
    ClientContactCreate, ClientContactUpdate,
    ClientJobCreate, ClientJobUpdate,
    ClientActivityCreate, ClientActivityUpdate
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
            # Check if client with same email already exists
            existing = await self.db.execute(
                select(Client).where(Client.company_email == client_data.company_email)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Client with email {client_data.company_email} already exists")
            
            # Create client
            client = Client(
                **client_data.model_dump(),
                created_by=created_by,
                status="active",
                is_active=True
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
                .options(
                    selectinload(Client.contacts),
                    selectinload(Client.jobs)
                )
                .where(Client.id == client_id)
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
    
    async def delete_client(self, client_id: str) -> bool:
        """Delete client (soft delete by deactivating)"""
        try:
            client = await self.get_client(client_id)
            if not client:
                raise ValueError(f"Client not found: {client_id}")
            
            client.status = "inactive"
            client.is_active = False
            client.deactivated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Deactivated client: {client.company_name} (ID: {client_id})")
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
                        Client.company_email.ilike(search_term),
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
            
            # Company size filter
            if filters.company_size:
                filter_conditions.append(Client.company_size.in_(filters.company_size))
            
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
                # Get counts
                contacts_count = len(client.contacts) if hasattr(client, 'contacts') else 0
                jobs_count = len(client.jobs) if hasattr(client, 'jobs') else 0
                active_jobs_count = sum(1 for job in client.jobs if job.status == 'open') if hasattr(client, 'jobs') else 0
                
                client_dict = {
                    **client.__dict__,
                    'contacts_count': contacts_count,
                    'jobs_count': jobs_count,
                    'active_jobs_count': active_jobs_count
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
    
    # ============================================================================
    # CLIENT CONTACT OPERATIONS
    # ============================================================================
    
    async def create_contact(self, contact_data: ClientContactCreate, created_by: str) -> ClientContact:
        """Create a new client contact"""
        try:
            # Verify client exists
            client = await self.get_client(contact_data.client_id)
            if not client:
                raise ValueError(f"Client not found: {contact_data.client_id}")
            
            # If this is primary contact, unset other primary contacts
            if contact_data.is_primary:
                await self.db.execute(
                    select(ClientContact)
                    .where(
                        ClientContact.client_id == contact_data.client_id,
                        ClientContact.is_primary == True
                    )
                )
                # Update existing primary contacts
                existing_primary = await self.db.execute(
                    select(ClientContact).where(
                        ClientContact.client_id == contact_data.client_id,
                        ClientContact.is_primary == True
                    )
                )
                for contact in existing_primary.scalars():
                    contact.is_primary = False
            
            # Create contact
            contact = ClientContact(
                **contact_data.model_dump(),
                created_by=created_by,
                is_active=True
            )
            
            self.db.add(contact)
            await self.db.commit()
            await self.db.refresh(contact)
            
            logger.info(f"Created contact: {contact.full_name} for client {contact_data.client_id}")
            return contact
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating contact: {str(e)}")
            raise
    
    async def get_client_contacts(self, client_id: str) -> List[ClientContact]:
        """Get all contacts for a client"""
        try:
            result = await self.db.execute(
                select(ClientContact)
                .where(ClientContact.client_id == client_id)
                .order_by(ClientContact.is_primary.desc(), ClientContact.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting client contacts: {str(e)}")
            raise
    
    async def update_contact(self, contact_id: str, contact_data: ClientContactUpdate) -> ClientContact:
        """Update client contact"""
        try:
            result = await self.db.execute(
                select(ClientContact).where(ClientContact.id == contact_id)
            )
            contact = result.scalar_one_or_none()
            
            if not contact:
                raise ValueError(f"Contact not found: {contact_id}")
            
            # Update fields
            update_data = contact_data.model_dump(exclude_unset=True)
            
            # If setting as primary, unset other primary contacts
            if update_data.get('is_primary'):
                existing_primary = await self.db.execute(
                    select(ClientContact).where(
                        ClientContact.client_id == contact.client_id,
                        ClientContact.is_primary == True,
                        ClientContact.id != contact_id
                    )
                )
                for existing in existing_primary.scalars():
                    existing.is_primary = False
            
            for field, value in update_data.items():
                setattr(contact, field, value)
            
            await self.db.commit()
            await self.db.refresh(contact)
            
            logger.info(f"Updated contact: {contact.full_name} (ID: {contact_id})")
            return contact
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating contact: {str(e)}")
            raise
    
    # ============================================================================
    # CLIENT JOB OPERATIONS
    # ============================================================================
    
    async def create_job(self, job_data: ClientJobCreate, created_by: str) -> ClientJob:
        """Create a new client job"""
        try:
            # Verify client exists
            client = await self.get_client(job_data.client_id)
            if not client:
                raise ValueError(f"Client not found: {job_data.client_id}")
            
            # Create job
            job = ClientJob(
                **job_data.model_dump(),
                created_by=created_by,
                status="open"
            )
            
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            
            logger.info(f"Created job: {job.job_title} for client {job_data.client_id}")
            return job
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    async def get_client_jobs(self, client_id: str, status: Optional[str] = None) -> List[ClientJob]:
        """Get all jobs for a client"""
        try:
            query = select(ClientJob).where(ClientJob.client_id == client_id)
            
            if status:
                query = query.where(ClientJob.status == status)
            
            query = query.order_by(ClientJob.created_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting client jobs: {str(e)}")
            raise
    
    # ============================================================================
    # CLIENT ACTIVITY OPERATIONS
    # ============================================================================
    
    async def create_activity(
        self,
        activity_data: ClientActivityCreate,
        performed_by: str
    ) -> ClientActivity:
        """Create a new client activity"""
        try:
            # Verify client exists
            client = await self.get_client(activity_data.client_id)
            if not client:
                raise ValueError(f"Client not found: {activity_data.client_id}")
            
            # Create activity
            activity = ClientActivity(
                **activity_data.model_dump(),
                performed_by=performed_by,
                status="completed" if not activity_data.scheduled_date else "scheduled"
            )
            
            self.db.add(activity)
            await self.db.commit()
            await self.db.refresh(activity)
            
            logger.info(f"Created activity: {activity.activity_title} for client {activity_data.client_id}")
            return activity
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating activity: {str(e)}")
            raise
    
    async def get_client_activities(
        self,
        client_id: str,
        limit: int = 50
    ) -> List[ClientActivity]:
        """Get recent activities for a client"""
        try:
            result = await self.db.execute(
                select(ClientActivity)
                .where(ClientActivity.client_id == client_id)
                .order_by(ClientActivity.activity_date.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting client activities: {str(e)}")
            raise
    
    # ============================================================================
    # STATISTICS & ANALYTICS
    # ============================================================================
    
    async def get_client_statistics(self) -> Dict[str, Any]:
        """Get overall client statistics"""
        try:
            # Total clients
            total_result = await self.db.execute(select(func.count(Client.id)))
            total_clients = total_result.scalar() or 0
            
            # Active clients
            active_result = await self.db.execute(
                select(func.count(Client.id)).where(Client.status == 'active')
            )
            active_clients = active_result.scalar() or 0
            
            # Clients with active jobs
            clients_with_jobs = await self.db.execute(
                select(func.count(func.distinct(ClientJob.client_id)))
                .where(ClientJob.status == 'open')
            )
            clients_with_active_jobs = clients_with_jobs.scalar() or 0
            
            return {
                "total_clients": total_clients,
                "active_clients": active_clients,
                "inactive_clients": total_clients - active_clients,
                "clients_with_active_jobs": clients_with_active_jobs
            }
            
        except Exception as e:
            logger.error(f"Error getting client statistics: {str(e)}")
            raise
