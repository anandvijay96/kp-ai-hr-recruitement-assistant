"""Service for job analytics calculations"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import logging

from models.database import Job, JobAnalytics, generate_uuid

logger = logging.getLogger(__name__)


class JobAnalyticsService:
    """Service for calculating and retrieving job analytics"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_job_analytics(
        self,
        job_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a job
        
        Args:
            job_id: Job ID
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with funnel metrics, conversion rates, quality metrics, trends
        
        Raises:
            ValueError: If job not found
        """
        try:
            # Verify job exists
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            # Set default date range (last 30 days)
            if not date_to:
                date_to = date.today().isoformat()
            if not date_from:
                date_from = (date.today() - timedelta(days=30)).isoformat()
            
            # Calculate funnel metrics
            funnel = await self._calculate_funnel_metrics(job_id, date_from, date_to)
            
            # Calculate conversion rates
            conversion_rates = self._calculate_conversion_rates(funnel)
            
            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(job_id, date_from, date_to)
            
            # Calculate time metrics
            time_metrics = await self._calculate_time_metrics(job_id)
            
            # Get trends data
            trends = await self._get_trends_data(job_id, date_from, date_to)
            
            # Get comparison metrics
            comparison = await self._get_comparison_metrics(job_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "date_range": {
                    "from": date_from,
                    "to": date_to
                },
                "funnel": funnel,
                "conversion_rates": conversion_rates,
                "quality_metrics": quality_metrics,
                "time_metrics": time_metrics,
                "trends": trends,
                "comparison": comparison
            }
        
        except Exception as e:
            logger.error(f"Error calculating analytics: {str(e)}", exc_info=True)
            raise
    
    async def _calculate_funnel_metrics(
        self,
        job_id: str,
        date_from: str,
        date_to: str
    ) -> Dict[str, int]:
        """Calculate funnel metrics from job_analytics table"""
        try:
            result = await self.db.execute(
                select(
                    func.sum(JobAnalytics.view_count).label('views'),
                    func.sum(JobAnalytics.application_count).label('applications'),
                    func.sum(JobAnalytics.shortlist_count).label('shortlisted'),
                    func.sum(JobAnalytics.interview_count).label('interviewed'),
                    func.sum(JobAnalytics.offer_count).label('offers'),
                    func.sum(JobAnalytics.hire_count).label('hires')
                )
                .where(
                    and_(
                        JobAnalytics.job_id == job_id,
                        JobAnalytics.date >= date_from,
                        JobAnalytics.date <= date_to
                    )
                )
            )
            row = result.first()
            
            return {
                "views": int(row.views or 0),
                "applications": int(row.applications or 0),
                "shortlisted": int(row.shortlisted or 0),
                "interviewed": int(row.interviewed or 0),
                "offers": int(row.offers or 0),
                "hires": int(row.hires or 0)
            }
        except Exception as e:
            logger.error(f"Error calculating funnel metrics: {str(e)}")
            # Return placeholder data if analytics not available
            return {
                "views": 0,
                "applications": 0,
                "shortlisted": 0,
                "interviewed": 0,
                "offers": 0,
                "hires": 0
            }
    
    def _calculate_conversion_rates(self, funnel: Dict[str, int]) -> Dict[str, float]:
        """Calculate conversion rates between funnel stages"""
        def safe_divide(numerator: int, denominator: int) -> float:
            return round((numerator / denominator * 100), 1) if denominator > 0 else 0.0
        
        return {
            "view_to_application": safe_divide(funnel["applications"], funnel["views"]),
            "application_to_shortlist": safe_divide(funnel["shortlisted"], funnel["applications"]),
            "shortlist_to_interview": safe_divide(funnel["interviewed"], funnel["shortlisted"]),
            "interview_to_offer": safe_divide(funnel["offers"], funnel["interviewed"]),
            "offer_to_hire": safe_divide(funnel["hires"], funnel["offers"])
        }
    
    async def _calculate_quality_metrics(
        self,
        job_id: str,
        date_from: str,
        date_to: str
    ) -> Dict[str, Any]:
        """Calculate quality metrics (match scores)"""
        # Placeholder - would query applications and calculate match score statistics
        return {
            "avg_match_score": None,
            "median_match_score": None,
            "match_score_distribution": {
                "90-100": 0,
                "80-89": 0,
                "70-79": 0,
                "60-69": 0,
                "below-60": 0
            }
        }
    
    async def _calculate_time_metrics(self, job_id: str) -> Dict[str, Optional[int]]:
        """Calculate time-based metrics"""
        try:
            result = await self.db.execute(
                select(JobAnalytics)
                .where(JobAnalytics.job_id == job_id)
                .order_by(JobAnalytics.date.desc())
                .limit(1)
            )
            latest = result.scalar_one_or_none()
            
            if latest:
                return {
                    "time_to_fill_days": latest.time_to_fill,
                    "time_to_first_application_hours": latest.time_to_first_application,
                    "avg_time_to_shortlist_days": None
                }
        except Exception as e:
            logger.error(f"Error calculating time metrics: {str(e)}")
        
        return {
            "time_to_fill_days": None,
            "time_to_first_application_hours": None,
            "avg_time_to_shortlist_days": None
        }
    
    async def _get_trends_data(
        self,
        job_id: str,
        date_from: str,
        date_to: str
    ) -> List[Dict[str, Any]]:
        """Get daily trends data"""
        try:
            result = await self.db.execute(
                select(JobAnalytics)
                .where(
                    and_(
                        JobAnalytics.job_id == job_id,
                        JobAnalytics.date >= date_from,
                        JobAnalytics.date <= date_to
                    )
                )
                .order_by(JobAnalytics.date.asc())
            )
            analytics = result.scalars().all()
            
            return [
                {
                    "date": a.date,
                    "applications": a.application_count,
                    "views": a.view_count
                }
                for a in analytics
            ]
        except Exception as e:
            logger.error(f"Error fetching trends data: {str(e)}")
            return []
    
    async def _get_comparison_metrics(self, job_id: str) -> Dict[str, Optional[float]]:
        """Get comparison with similar jobs"""
        # Placeholder - would query similar jobs (same department/role) and calculate averages
        return {
            "similar_jobs_avg_match_score": None,
            "similar_jobs_avg_time_to_fill": None
        }
    
    async def update_daily_analytics(
        self,
        job_id: str,
        analytics_date: date,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Update daily analytics for a job
        This would be called by a scheduled task
        
        Args:
            job_id: Job ID
            analytics_date: Date for analytics
            metrics: Dictionary of metrics to update
        """
        try:
            # Check if record exists
            result = await self.db.execute(
                select(JobAnalytics).where(
                    and_(
                        JobAnalytics.job_id == job_id,
                        JobAnalytics.date == analytics_date.isoformat()
                    )
                )
            )
            analytics = result.scalar_one_or_none()
            
            if analytics:
                # Update existing record
                for key, value in metrics.items():
                    setattr(analytics, key, value)
                analytics.updated_at = datetime.utcnow()
            else:
                # Create new record
                analytics = JobAnalytics(
                    id=generate_uuid(),
                    job_id=job_id,
                    date=analytics_date.isoformat(),
                    **metrics
                )
                self.db.add(analytics)
            
            await self.db.commit()
            logger.info(f"Updated analytics for job {job_id} on {analytics_date}")
        
        except Exception as e:
            logger.error(f"Error updating daily analytics: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise
