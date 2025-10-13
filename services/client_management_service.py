"""Client management service"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from models.database import Client, ClientContact, User, ClientJobAssignment, Job
from models.client_schemas import (
    ClientCreateRequest, ClientUpdateRequest, ClientDeactivateRequest,
    ClientContactCreate
)

logger = logging.getLogger(__name__)


class ClientManagementService:
    """Service for managing clients"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def generate_client_code(self) -> str:
        """
        Generate unique client code in format CLT-YYYY-XXXX
        
        Returns:
            Client code string
        """
        try:
            year = datetime.now().year
            prefix = f"CLT-{year}-"
            
            # Get the latest client code for this year
            query = select(Client.client_code).where(
                Client.client_code.like(f"{prefix}%")
            ).order_by(Client.client_code.desc()).limit(1)
            
            result = await self.db.execute(query)
            latest_code = result.scalar()
            
            if latest_code:
                # Extract number and increment
                num = int(latest_code.split('-')[-1])
                new_num = num + 1
            else:
                new_num = 1
            
            return f"{prefix}{new_num:04d}"
            
        except Exception as e:
            logger.error(f"Error generating client code: {e}")
            # Fallback to timestamp-based code
            import time
            return f"CLT-{year}-{int(time.time() % 10000):04d}"
    
    async def check_duplicate_client(
        self, 
        name: str, 
        email_domain: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check for duplicate clients by name or email domain
        
        Args:
            name: Client name
            email_domain: Email domain from contact email
            
        Returns:
            Duplicate client info or None
        """
        try:
            # Check by exact name match (case-insensitive)
            query = select(Client).where(
                and_(
                    func.lower(Client.name) == name.lower(),
                    Client.status != 'archived'
                )
            )
            
            result = await self.db.execute(query)
            existing_client = result.scalar_one_or_none()
            
            if existing_client:
                return {
                    "id": existing_client.id,
                    "name": existing_client.name,
                    "client_code": existing_client.client_code,
                    "match_type": "exact_name"
                }
            
            # TODO: Check by email domain if needed
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking duplicate client: {e}")
            return None
    
    async def create_client(
        self, 
        data: ClientCreateRequest, 
        current_user: User
    ) -> Client:
        """
        Create a new client with contacts
        
        Args:
            data: Client creation data
            current_user: User creating the client
            
        Returns:
            Created client
        """
        try:
            # Check for duplicates
            duplicate = await self.check_duplicate_client(data.name)
            if duplicate:
                raise ValueError(f"Client with name '{data.name}' already exists (Code: {duplicate['client_code']})")
            
            # Generate client code
            client_code = await self.generate_client_code()
            
            # Create client
            client = Client(
                client_code=client_code,
                name=data.name,
                industry=data.industry,
                website=str(data.website) if data.website else None,
                address=data.address,
                city=data.city,
                state=data.state,
                country=data.country,
                postal_code=data.postal_code,
                account_manager_id=data.account_manager_id,
                created_by=current_user.id,
                status='active'
            )
            
            self.db.add(client)
            await self.db.flush()  # Get client ID
            
            # Create contacts
            for idx, contact_data in enumerate(data.contacts):
                contact = ClientContact(
                    client_id=client.id,
                    full_name=contact_data.full_name,
                    title=contact_data.title,
                    email=contact_data.email,
                    phone=contact_data.phone,
                    mobile=contact_data.mobile,
                    is_primary=contact_data.is_primary,
                    is_active=True
                )
                self.db.add(contact)
            
            await self.db.commit()
            await self.db.refresh(client)
            
            logger.info(f"Client created: {client.client_code} by user {current_user.id}")
            return client
            
        except ValueError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating client: {e}")
            raise Exception(f"Failed to create client: {str(e)}")
    
    async def list_clients(
        self,
        status: Optional[str] = None,
        industry: Optional[str] = None,
        account_manager_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List clients with filtering and pagination
        
        Args:
            status: Filter by status
            industry: Filter by industry
            account_manager_id: Filter by account manager
            search: Search by name or client code
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
            page: Page number
            limit: Items per page
            
        Returns:
            Dictionary with clients, pagination, and summary
        """
        try:
            from sqlalchemy.orm import selectinload
            
            # Build query with account_manager loaded
            query = select(Client).options(selectinload(Client.account_manager))
            
            # Apply filters
            if status:
                query = query.where(Client.status == status)
            if industry:
                query = query.where(Client.industry == industry)
            if account_manager_id:
                query = query.where(Client.account_manager_id == account_manager_id)
            if search:
                search_term = f"%{search.lower()}%"
                query = query.where(
                    or_(
                        func.lower(Client.name).like(search_term),
                        func.lower(Client.client_code).like(search_term)
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply sorting
            sort_column = getattr(Client, sort_by, Client.created_at)
            if sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            clients = result.scalars().all()
            
            # Get summary statistics
            summary = await self._get_client_summary()
            
            return {
                "clients": clients,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit
                },
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            raise Exception(f"Failed to list clients: {str(e)}")
    
    async def _get_client_summary(self) -> Dict[str, int]:
        """Get summary statistics for clients"""
        try:
            # Count by status
            query = select(
                Client.status,
                func.count(Client.id)
            ).group_by(Client.status)
            
            result = await self.db.execute(query)
            status_counts = dict(result.all())
            
            return {
                "active": status_counts.get("active", 0),
                "inactive": status_counts.get("inactive", 0),
                "on_hold": status_counts.get("on-hold", 0),
                "archived": status_counts.get("archived", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting client summary: {e}")
            return {"active": 0, "inactive": 0, "on_hold": 0, "archived": 0}
    
    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """
        Get client by ID with related data
        
        Args:
            client_id: Client ID
            
        Returns:
            Client or None
        """
        try:
            query = select(Client).where(Client.id == client_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting client: {e}")
            return None
    
    async def get_client_contacts(self, client_id: str) -> List[ClientContact]:
        """
        Get all contacts for a client
        
        Args:
            client_id: Client ID
            
        Returns:
            List of contacts
        """
        try:
            query = select(ClientContact).where(
                and_(
                    ClientContact.client_id == client_id,
                    ClientContact.is_active == True
                )
            ).order_by(ClientContact.is_primary.desc(), ClientContact.full_name)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting client contacts: {e}")
            return []
    
    async def update_client(
        self, 
        client_id: str, 
        data: ClientUpdateRequest, 
        current_user: User
    ) -> Client:
        """
        Update client information
        
        Args:
            client_id: Client ID
            data: Update data
            current_user: User performing update
            
        Returns:
            Updated client
        """
        try:
            client = await self.get_client_by_id(client_id)
            if not client:
                raise ValueError(f"Client not found: {client_id}")
            
            # Update fields
            if data.name is not None:
                client.name = data.name
            if data.industry is not None:
                client.industry = data.industry
            if data.website is not None:
                client.website = str(data.website) if data.website else None
            if data.address is not None:
                client.address = data.address
            if data.city is not None:
                client.city = data.city
            if data.state is not None:
                client.state = data.state
            if data.country is not None:
                client.country = data.country
            if data.postal_code is not None:
                client.postal_code = data.postal_code
            if data.account_manager_id is not None:
                client.account_manager_id = data.account_manager_id
            if data.status is not None:
                client.status = data.status.value
            
            client.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(client)
            
            logger.info(f"Client updated: {client.client_code} by user {current_user.id}")
            return client
            
        except ValueError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating client: {e}")
            raise Exception(f"Failed to update client: {str(e)}")
    
    async def deactivate_client(
        self, 
        client_id: str, 
        data: ClientDeactivateRequest, 
        current_user: User
    ) -> Client:
        """
        Deactivate a client (Admin only)
        
        Args:
            client_id: Client ID
            data: Deactivation data
            current_user: User performing deactivation
            
        Returns:
            Deactivated client
        """
        try:
            client = await self.get_client_by_id(client_id)
            if not client:
                raise ValueError(f"Client not found: {client_id}")
            
            if client.status == 'inactive':
                raise ValueError("Client is already deactivated")
            
            client.status = 'inactive'
            client.deactivated_at = datetime.now()
            client.deactivation_reason = f"{data.reason}"
            if data.reason_details:
                client.deactivation_reason += f": {data.reason_details}"
            
            await self.db.commit()
            await self.db.refresh(client)
            
            logger.info(f"Client deactivated: {client.client_code} by user {current_user.id}")
            return client
            
        except ValueError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deactivating client: {e}")
            raise Exception(f"Failed to deactivate client: {str(e)}")
    
    async def reactivate_client(self, client_id: str, current_user: User) -> Client:
        """
        Reactivate a deactivated client
        
        Args:
            client_id: Client ID
            current_user: User performing reactivation
            
        Returns:
            Reactivated client
        """
        try:
            client = await self.get_client_by_id(client_id)
            if not client:
                raise ValueError(f"Client not found: {client_id}")
            
            if client.status != 'inactive':
                raise ValueError("Client is not deactivated")
            
            client.status = 'active'
            client.deactivated_at = None
            client.deactivation_reason = None
            
            await self.db.commit()
            await self.db.refresh(client)
            
            logger.info(f"Client reactivated: {client.client_code} by user {current_user.id}")
            return client
            
        except ValueError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error reactivating client: {e}")
            raise Exception(f"Failed to reactivate client: {str(e)}")
    
    async def add_contact(
        self, 
        client_id: str, 
        contact_data: ClientContactCreate
    ) -> ClientContact:
        """
        Add a contact person to a client
        
        Args:
            client_id: Client ID
            contact_data: Contact data
            
        Returns:
            Created contact
        """
        try:
            client = await self.get_client_by_id(client_id)
            if not client:
                raise ValueError(f"Client not found: {client_id}")
            
            # If this is set as primary, unset other primary contacts
            if contact_data.is_primary:
                query = select(ClientContact).where(
                    and_(
                        ClientContact.client_id == client_id,
                        ClientContact.is_primary == True
                    )
                )
                result = await self.db.execute(query)
                existing_primary = result.scalars().all()
                for contact in existing_primary:
                    contact.is_primary = False
            
            contact = ClientContact(
                client_id=client_id,
                full_name=contact_data.full_name,
                title=contact_data.title,
                email=contact_data.email,
                phone=contact_data.phone,
                mobile=contact_data.mobile,
                is_primary=contact_data.is_primary,
                is_active=True
            )
            
            self.db.add(contact)
            await self.db.commit()
            await self.db.refresh(contact)
            
            logger.info(f"Contact added to client {client.client_code}")
            return contact
            
        except ValueError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding contact: {e}")
            raise Exception(f"Failed to add contact: {str(e)}")
    
    async def get_account_managers(self) -> List[User]:
        """
        Get list of users who can be account managers (managers and admins)
        
        Returns:
            List of users
        """
        try:
            query = select(User).where(
                and_(
                    User.role.in_(['admin', 'manager']),
                    User.is_active == True
                )
            ).order_by(User.full_name)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting account managers: {e}")
            return []
