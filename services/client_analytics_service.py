"""Client analytics service"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from models.database import (
    ClientAnalytics, Client, ClientJobAssignment, Job,
    ClientCommunication, Candidate
)

logger = logging.getLogger(__name__)


class ClientAnalyticsService:
    """Service for client analytics and dashboard data"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_dashboard_data(self, client_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a client
        
        Args:
            client_id: Client ID
            
        Returns:
            Dictionary with stats, activities, and pipeline
        """
        try:
            stats = await self._get_client_stats(client_id)
            recent_activities = await self._get_recent_activities(client_id, limit=10)
            pipeline_summary = await self._get_pipeline_summary(client_id)
            
            return {
                "stats": stats,
                "recent_activities": recent_activities,
                "pipeline_summary": pipeline_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise Exception(f"Failed to get dashboard data: {str(e)}")
    
    async def _get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get key statistics for a client"""
        try:
            # Count active jobs
            active_jobs_query = select(func.count(ClientJobAssignment.id)).where(
                and_(
                    ClientJobAssignment.client_id == client_id,
                    ClientJobAssignment.is_active == True
                )
            )
            active_jobs_result = await self.db.execute(active_jobs_query)
            active_jobs = active_jobs_result.scalar() or 0
            
            # Get latest analytics
            analytics_query = select(ClientAnalytics).where(
                ClientAnalytics.client_id == client_id
            ).order_by(ClientAnalytics.date.desc()).limit(1)
            analytics_result = await self.db.execute(analytics_query)
            latest_analytics = analytics_result.scalar_one_or_none()
            
            if latest_analytics:
                return {
                    "active_jobs": active_jobs,
                    "total_candidates": latest_analytics.total_candidates_count,
                    "hires": latest_analytics.hired_count,
                    "avg_time_to_fill": latest_analytics.avg_time_to_fill_days or 0
                }
            else:
                return {
                    "active_jobs": active_jobs,
                    "total_candidates": 0,
                    "hires": 0,
                    "avg_time_to_fill": 0
                }
            
        except Exception as e:
            logger.error(f"Error getting client stats: {e}")
            return {
                "active_jobs": 0,
                "total_candidates": 0,
                "hires": 0,
                "avg_time_to_fill": 0
            }
    
    async def _get_recent_activities(
        self,
        client_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activities for a client"""
        try:
            activities = []
            
            # Get recent communications
            comm_query = select(ClientCommunication).where(
                ClientCommunication.client_id == client_id
            ).order_by(ClientCommunication.communication_date.desc()).limit(limit)
            
            comm_result = await self.db.execute(comm_query)
            communications = comm_result.scalars().all()
            
            for comm in communications:
                activities.append({
                    "type": "communication",
                    "description": f"{comm.communication_type}: {comm.subject or 'No subject'}",
                    "date": comm.communication_date,
                    "important": comm.is_important
                })
            
            # Sort by date
            activities.sort(key=lambda x: x["date"], reverse=True)
            
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []
    
    async def _get_pipeline_summary(self, client_id: str) -> Dict[str, int]:
        """Get candidate pipeline summary for a client"""
        try:
            # Get latest analytics
            query = select(ClientAnalytics).where(
                ClientAnalytics.client_id == client_id
            ).order_by(ClientAnalytics.date.desc()).limit(1)
            
            result = await self.db.execute(query)
            analytics = result.scalar_one_or_none()
            
            if analytics:
                return {
                    "screened": analytics.screened_count,
                    "shortlisted": analytics.shortlisted_count,
                    "interviewed": analytics.interviewed_count,
                    "hired": analytics.hired_count
                }
            else:
                return {
                    "screened": 0,
                    "shortlisted": 0,
                    "interviewed": 0,
                    "hired": 0
                }
            
        except Exception as e:
            logger.error(f"Error getting pipeline summary: {e}")
            return {
                "screened": 0,
                "shortlisted": 0,
                "interviewed": 0,
                "hired": 0
            }
    
    async def aggregate_daily_analytics(
        self,
        client_id: str,
        target_date: Optional[date] = None
    ) -> ClientAnalytics:
        """
        Aggregate analytics for a client for a specific date
        
        Args:
            client_id: Client ID
            target_date: Date to aggregate (defaults to today)
            
        Returns:
            Created/updated analytics record
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Count active jobs
            active_jobs_query = select(func.count(ClientJobAssignment.id)).where(
                and_(
                    ClientJobAssignment.client_id == client_id,
                    ClientJobAssignment.is_active == True
                )
            )
            active_jobs_result = await self.db.execute(active_jobs_query)
            active_jobs_count = active_jobs_result.scalar() or 0
            
            # Check if analytics for this date already exists
            existing_query = select(ClientAnalytics).where(
                and_(
                    ClientAnalytics.client_id == client_id,
                    ClientAnalytics.date == target_date
                )
            )
            existing_result = await self.db.execute(existing_query)
            analytics = existing_result.scalar_one_or_none()
            
            if analytics:
                # Update existing record
                analytics.active_jobs_count = active_jobs_count
                analytics.updated_at = datetime.now()
            else:
                # Create new record
                analytics = ClientAnalytics(
                    client_id=client_id,
                    date=target_date,
                    active_jobs_count=active_jobs_count,
                    total_candidates_count=0,
                    screened_count=0,
                    shortlisted_count=0,
                    interviewed_count=0,
                    hired_count=0
                )
                self.db.add(analytics)
            
            await self.db.commit()
            await self.db.refresh(analytics)
            
            logger.info(f"Analytics aggregated for client {client_id} on {target_date}")
            return analytics
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error aggregating analytics: {e}")
            raise Exception(f"Failed to aggregate analytics: {str(e)}")
