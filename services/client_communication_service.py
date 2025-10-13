"""Client communication service"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from models.database import ClientCommunication, Client, User
from models.client_schemas import CommunicationCreateRequest

logger = logging.getLogger(__name__)


class ClientCommunicationService:
    """Service for client communication tracking"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def log_communication(
        self,
        client_id: str,
        data: CommunicationCreateRequest,
        current_user: User
    ) -> ClientCommunication:
        """
        Log a communication with a client
        
        Args:
            client_id: Client ID
            data: Communication data
            current_user: User logging the communication
            
        Returns:
            Created communication record
        """
        try:
            communication = ClientCommunication(
                client_id=client_id,
                communication_type=data.communication_type.value,
                subject=data.subject,
                notes=data.notes,
                communication_date=data.communication_date,
                participants=data.participants,
                job_reference_id=data.job_reference_id,
                logged_by=current_user.id,
                is_important=data.is_important,
                follow_up_required=data.follow_up_required,
                follow_up_date=data.follow_up_date,
                attachments=[]
            )
            
            self.db.add(communication)
            await self.db.commit()
            await self.db.refresh(communication)
            
            logger.info(f"Communication logged for client {client_id} by user {current_user.id}")
            return communication
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error logging communication: {e}")
            raise Exception(f"Failed to log communication: {str(e)}")
    
    async def list_communications(
        self,
        client_id: str,
        communication_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        important_only: bool = False,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List communications for a client with filtering
        
        Args:
            client_id: Client ID
            communication_type: Filter by type
            date_from: Start date filter
            date_to: End date filter
            important_only: Only important communications
            page: Page number
            limit: Items per page
            
        Returns:
            Dictionary with communications and pagination
        """
        try:
            query = select(ClientCommunication).where(
                ClientCommunication.client_id == client_id
            )
            
            # Apply filters
            if communication_type:
                query = query.where(ClientCommunication.communication_type == communication_type)
            if date_from:
                query = query.where(ClientCommunication.communication_date >= date_from)
            if date_to:
                query = query.where(ClientCommunication.communication_date <= date_to)
            if important_only:
                query = query.where(ClientCommunication.is_important == True)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply sorting and pagination
            query = query.order_by(ClientCommunication.communication_date.desc())
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            communications = result.scalars().all()
            
            return {
                "communications": communications,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing communications: {e}")
            raise Exception(f"Failed to list communications: {str(e)}")
    
    async def add_attachment(
        self,
        communication_id: str,
        file_info: Dict[str, Any]
    ) -> ClientCommunication:
        """
        Add an attachment to a communication
        
        Args:
            communication_id: Communication ID
            file_info: File information dict
            
        Returns:
            Updated communication
        """
        try:
            query = select(ClientCommunication).where(
                ClientCommunication.id == communication_id
            )
            result = await self.db.execute(query)
            communication = result.scalar_one_or_none()
            
            if not communication:
                raise ValueError(f"Communication not found: {communication_id}")
            
            # Add attachment to JSON array
            attachments = communication.attachments or []
            attachments.append(file_info)
            communication.attachments = attachments
            
            await self.db.commit()
            await self.db.refresh(communication)
            
            logger.info(f"Attachment added to communication {communication_id}")
            return communication
            
        except ValueError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding attachment: {e}")
            raise Exception(f"Failed to add attachment: {str(e)}")
