"""Client feedback service"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from models.database import ClientFeedback, Client, User
from models.client_schemas import FeedbackCreateRequest

logger = logging.getLogger(__name__)


class ClientFeedbackService:
    """Service for client feedback management"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def submit_feedback(
        self,
        client_id: str,
        data: FeedbackCreateRequest,
        current_user: User
    ) -> ClientFeedback:
        """
        Submit feedback for a client
        
        Args:
            client_id: Client ID
            data: Feedback data
            current_user: User submitting feedback
            
        Returns:
            Created feedback record
        """
        try:
            feedback = ClientFeedback(
                client_id=client_id,
                feedback_period=data.feedback_period,
                feedback_date=data.feedback_date,
                responsiveness_rating=data.responsiveness_rating,
                communication_rating=data.communication_rating,
                requirements_clarity_rating=data.requirements_clarity_rating,
                decision_speed_rating=data.decision_speed_rating,
                overall_satisfaction=data.overall_satisfaction,
                written_feedback=data.written_feedback,
                submitted_by=current_user.id,
                is_finalized=False
            )
            
            self.db.add(feedback)
            await self.db.commit()
            await self.db.refresh(feedback)
            
            logger.info(f"Feedback submitted for client {client_id} by user {current_user.id}")
            return feedback
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error submitting feedback: {e}")
            raise Exception(f"Failed to submit feedback: {str(e)}")
    
    async def list_feedback(
        self,
        client_id: str
    ) -> Dict[str, Any]:
        """
        List all feedback for a client with averages
        
        Args:
            client_id: Client ID
            
        Returns:
            Dictionary with feedback records and averages
        """
        try:
            query = select(ClientFeedback).where(
                ClientFeedback.client_id == client_id
            ).order_by(ClientFeedback.feedback_date.desc())
            
            result = await self.db.execute(query)
            feedback_records = result.scalars().all()
            
            # Calculate averages
            averages = await self.calculate_averages(client_id)
            
            # Determine trend (simple logic: compare latest vs previous)
            trend = "stable"
            if len(feedback_records) >= 2:
                latest = feedback_records[0].overall_satisfaction
                previous = feedback_records[1].overall_satisfaction
                if latest > previous:
                    trend = "improving"
                elif latest < previous:
                    trend = "declining"
            
            return {
                "feedback_records": feedback_records,
                "average_ratings": averages,
                "trend": trend
            }
            
        except Exception as e:
            logger.error(f"Error listing feedback: {e}")
            raise Exception(f"Failed to list feedback: {str(e)}")
    
    async def calculate_averages(
        self,
        client_id: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, float]:
        """
        Calculate average ratings for a client
        
        Args:
            client_id: Client ID
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            Dictionary with average ratings
        """
        try:
            query = select(
                func.avg(ClientFeedback.responsiveness_rating),
                func.avg(ClientFeedback.communication_rating),
                func.avg(ClientFeedback.requirements_clarity_rating),
                func.avg(ClientFeedback.decision_speed_rating),
                func.avg(ClientFeedback.overall_satisfaction)
            ).where(ClientFeedback.client_id == client_id)
            
            if date_from:
                query = query.where(ClientFeedback.feedback_date >= date_from)
            if date_to:
                query = query.where(ClientFeedback.feedback_date <= date_to)
            
            result = await self.db.execute(query)
            averages = result.one()
            
            return {
                "responsiveness": round(averages[0] or 0, 2),
                "communication": round(averages[1] or 0, 2),
                "requirements_clarity": round(averages[2] or 0, 2),
                "decision_speed": round(averages[3] or 0, 2),
                "overall_satisfaction": round(averages[4] or 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating averages: {e}")
            return {
                "responsiveness": 0,
                "communication": 0,
                "requirements_clarity": 0,
                "decision_speed": 0,
                "overall_satisfaction": 0
            }
    
    async def finalize_feedback(
        self,
        feedback_id: str,
        current_user: User
    ) -> ClientFeedback:
        """
        Finalize feedback (Manager only)
        
        Args:
            feedback_id: Feedback ID
            current_user: User finalizing feedback
            
        Returns:
            Finalized feedback
        """
        try:
            query = select(ClientFeedback).where(ClientFeedback.id == feedback_id)
            result = await self.db.execute(query)
            feedback = result.scalar_one_or_none()
            
            if not feedback:
                raise ValueError(f"Feedback not found: {feedback_id}")
            
            if feedback.is_finalized:
                raise ValueError("Feedback is already finalized")
            
            feedback.is_finalized = True
            feedback.finalized_by = current_user.id
            feedback.finalized_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(feedback)
            
            logger.info(f"Feedback finalized: {feedback_id} by user {current_user.id}")
            return feedback
            
        except ValueError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error finalizing feedback: {e}")
            raise Exception(f"Failed to finalize feedback: {str(e)}")
