"""
Activity Tracking Service - Phase 3
====================================
Aggregates user activity data into daily, weekly, and monthly statistics.

Features:
- Real-time activity aggregation
- Daily/weekly/monthly rollups
- Performance metrics calculation
- Team analytics and rankings
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import (
    UserActivityLog,
    UserDailyStats,
    UserWeeklyStats,
    UserMonthlyStats,
    User
)
import uuid

logger = logging.getLogger(__name__)


class ActivityTracker:
    """Service for tracking and aggregating user activity"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def aggregate_daily_stats(self, user_id: str, target_date: date) -> UserDailyStats:
        """
        Aggregate activity logs into daily statistics for a specific user and date.
        
        Args:
            user_id: User ID to aggregate stats for
            target_date: Date to aggregate stats for
        
        Returns:
            UserDailyStats object
        """
        # Get or create daily stats record
        result = await self.session.execute(
            select(UserDailyStats).where(
                and_(
                    UserDailyStats.user_id == user_id,
                    UserDailyStats.date == target_date
                )
            )
        )
        daily_stats = result.scalar_one_or_none()
        
        if not daily_stats:
            daily_stats = UserDailyStats(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=target_date
            )
            self.session.add(daily_stats)
        
        # Query activity logs for this user and date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        result = await self.session.execute(
            select(UserActivityLog).where(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.timestamp >= start_datetime,
                    UserActivityLog.timestamp <= end_datetime,
                    UserActivityLog.status == "success"  # Only count successful actions
                )
            )
        )
        activities = result.scalars().all()
        
        # Aggregate counts by action type
        action_counts = {}
        total_duration = 0
        
        for activity in activities:
            action_type = activity.action_type
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            if activity.duration_ms:
                total_duration += activity.duration_ms
        
        # Update daily stats
        daily_stats.logins_count = action_counts.get("login", 0)
        daily_stats.resumes_vetted = action_counts.get("vet_resume", 0) + action_counts.get("batch_vet_resumes", 0)
        daily_stats.candidates_viewed = action_counts.get("view_candidate", 0)
        daily_stats.candidates_created = action_counts.get("create_candidate", 0)
        daily_stats.candidates_updated = action_counts.get("update_candidate", 0)
        daily_stats.searches_performed = action_counts.get("search_candidates", 0) + action_counts.get("search_jobs", 0)
        daily_stats.reports_generated = action_counts.get("generate_report", 0)
        daily_stats.jobs_created = action_counts.get("create_job", 0)
        daily_stats.jobs_updated = action_counts.get("update_job", 0)
        daily_stats.interviews_scheduled = action_counts.get("schedule_interview", 0)
        daily_stats.emails_sent = action_counts.get("send_email", 0)
        
        # Calculate session metrics
        daily_stats.total_actions = len(activities)
        daily_stats.total_session_time = total_duration // 1000  # Convert ms to seconds
        
        if daily_stats.logins_count > 0:
            daily_stats.avg_session_duration = daily_stats.total_session_time // daily_stats.logins_count
        
        await self.session.commit()
        await self.session.refresh(daily_stats)
        
        logger.info(f"Aggregated daily stats for user {user_id} on {target_date}: {daily_stats.total_actions} actions")
        
        return daily_stats
    
    async def aggregate_weekly_stats(self, user_id: str, year: int, week_number: int) -> UserWeeklyStats:
        """
        Aggregate daily stats into weekly statistics.
        
        Args:
            user_id: User ID to aggregate stats for
            year: Year
            week_number: ISO week number (1-53)
        
        Returns:
            UserWeeklyStats object
        """
        # Calculate week start and end dates
        week_start = datetime.strptime(f'{year}-W{week_number:02d}-1', "%Y-W%W-%w").date()
        week_end = week_start + timedelta(days=6)
        
        # Get or create weekly stats record
        result = await self.session.execute(
            select(UserWeeklyStats).where(
                and_(
                    UserWeeklyStats.user_id == user_id,
                    UserWeeklyStats.year == year,
                    UserWeeklyStats.week_number == week_number
                )
            )
        )
        weekly_stats = result.scalar_one_or_none()
        
        if not weekly_stats:
            weekly_stats = UserWeeklyStats(
                id=str(uuid.uuid4()),
                user_id=user_id,
                year=year,
                week_number=week_number,
                week_start_date=week_start,
                week_end_date=week_end
            )
            self.session.add(weekly_stats)
        
        # Query daily stats for this week
        result = await self.session.execute(
            select(UserDailyStats).where(
                and_(
                    UserDailyStats.user_id == user_id,
                    UserDailyStats.date >= week_start,
                    UserDailyStats.date <= week_end
                )
            )
        )
        daily_stats_list = result.scalars().all()
        
        # Aggregate daily stats
        weekly_stats.logins_count = sum(ds.logins_count for ds in daily_stats_list)
        weekly_stats.resumes_vetted = sum(ds.resumes_vetted for ds in daily_stats_list)
        weekly_stats.candidates_viewed = sum(ds.candidates_viewed for ds in daily_stats_list)
        weekly_stats.candidates_created = sum(ds.candidates_created for ds in daily_stats_list)
        weekly_stats.searches_performed = sum(ds.searches_performed for ds in daily_stats_list)
        weekly_stats.reports_generated = sum(ds.reports_generated for ds in daily_stats_list)
        weekly_stats.jobs_created = sum(ds.jobs_created for ds in daily_stats_list)
        weekly_stats.interviews_scheduled = sum(ds.interviews_scheduled for ds in daily_stats_list)
        weekly_stats.total_session_time = sum(ds.total_session_time for ds in daily_stats_list)
        
        # Calculate averages
        days_with_activity = len([ds for ds in daily_stats_list if ds.total_actions > 0])
        if days_with_activity > 0:
            total_actions = sum(ds.total_actions for ds in daily_stats_list)
            weekly_stats.avg_daily_actions = total_actions // days_with_activity
        
        # Calculate productivity score (0-100)
        weekly_stats.productivity_score = self._calculate_productivity_score(weekly_stats)
        
        await self.session.commit()
        await self.session.refresh(weekly_stats)
        
        logger.info(f"Aggregated weekly stats for user {user_id} for week {week_number}/{year}")
        
        return weekly_stats
    
    async def aggregate_monthly_stats(self, user_id: str, year: int, month: int) -> UserMonthlyStats:
        """
        Aggregate daily stats into monthly statistics.
        
        Args:
            user_id: User ID to aggregate stats for
            year: Year
            month: Month (1-12)
        
        Returns:
            UserMonthlyStats object
        """
        # Get or create monthly stats record
        result = await self.session.execute(
            select(UserMonthlyStats).where(
                and_(
                    UserMonthlyStats.user_id == user_id,
                    UserMonthlyStats.year == year,
                    UserMonthlyStats.month == month
                )
            )
        )
        monthly_stats = result.scalar_one_or_none()
        
        if not monthly_stats:
            monthly_stats = UserMonthlyStats(
                id=str(uuid.uuid4()),
                user_id=user_id,
                year=year,
                month=month
            )
            self.session.add(monthly_stats)
        
        # Query daily stats for this month
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        result = await self.session.execute(
            select(UserDailyStats).where(
                and_(
                    UserDailyStats.user_id == user_id,
                    UserDailyStats.date >= month_start,
                    UserDailyStats.date <= month_end
                )
            )
        )
        daily_stats_list = result.scalars().all()
        
        # Aggregate daily stats
        monthly_stats.logins_count = sum(ds.logins_count for ds in daily_stats_list)
        monthly_stats.resumes_vetted = sum(ds.resumes_vetted for ds in daily_stats_list)
        monthly_stats.candidates_viewed = sum(ds.candidates_viewed for ds in daily_stats_list)
        monthly_stats.candidates_created = sum(ds.candidates_created for ds in daily_stats_list)
        monthly_stats.searches_performed = sum(ds.searches_performed for ds in daily_stats_list)
        monthly_stats.reports_generated = sum(ds.reports_generated for ds in daily_stats_list)
        monthly_stats.jobs_created = sum(ds.jobs_created for ds in daily_stats_list)
        monthly_stats.interviews_scheduled = sum(ds.interviews_scheduled for ds in daily_stats_list)
        monthly_stats.total_session_time = sum(ds.total_session_time for ds in daily_stats_list)
        
        # Calculate averages
        days_with_activity = len([ds for ds in daily_stats_list if ds.total_actions > 0])
        if days_with_activity > 0:
            total_actions = sum(ds.total_actions for ds in daily_stats_list)
            monthly_stats.avg_daily_actions = total_actions // days_with_activity
        
        # Calculate scores
        monthly_stats.productivity_score = self._calculate_productivity_score(monthly_stats)
        monthly_stats.quality_score = await self._calculate_quality_score(user_id, month_start, month_end)
        
        # Calculate team rank
        monthly_stats.team_rank = await self._calculate_team_rank(user_id, year, month)
        
        await self.session.commit()
        await self.session.refresh(monthly_stats)
        
        logger.info(f"Aggregated monthly stats for user {user_id} for {month}/{year}")
        
        return monthly_stats
    
    def _calculate_productivity_score(self, stats) -> int:
        """
        Calculate productivity score (0-100) based on activity metrics.
        
        Formula considers:
        - Number of actions performed
        - Variety of actions
        - Consistency (session time)
        """
        score = 0
        
        # Base score from total actions (max 40 points)
        total_actions = (
            stats.resumes_vetted +
            stats.candidates_viewed +
            stats.candidates_created +
            stats.searches_performed +
            stats.jobs_created +
            stats.interviews_scheduled
        )
        score += min(40, total_actions // 2)  # 1 point per 2 actions, max 40
        
        # Variety score (max 30 points)
        action_types = [
            stats.resumes_vetted > 0,
            stats.candidates_viewed > 0,
            stats.candidates_created > 0,
            stats.searches_performed > 0,
            stats.jobs_created > 0,
            stats.interviews_scheduled > 0
        ]
        variety = sum(action_types)
        score += variety * 5  # 5 points per action type
        
        # Consistency score (max 30 points)
        if stats.logins_count > 0:
            avg_session = stats.total_session_time // stats.logins_count
            # Award points for reasonable session times (15-120 minutes)
            if 900 <= avg_session <= 7200:  # 15 min to 2 hours
                score += 30
            elif avg_session < 900:
                score += (avg_session // 30)  # Partial credit for shorter sessions
        
        return min(100, score)
    
    async def _calculate_quality_score(self, user_id: str, start_date: date, end_date: date) -> int:
        """
        Calculate quality score (0-100) based on decision accuracy.
        
        This is a placeholder - implement based on your quality metrics:
        - Candidate acceptance rate
        - Interview success rate
        - Hiring conversion rate
        """
        # TODO: Implement quality scoring logic
        # For now, return a default score
        return 75
    
    async def _calculate_team_rank(self, user_id: str, year: int, month: int) -> int:
        """Calculate user's rank within their team for the month"""
        # Get all monthly stats for this period
        result = await self.session.execute(
            select(UserMonthlyStats).where(
                and_(
                    UserMonthlyStats.year == year,
                    UserMonthlyStats.month == month
                )
            ).order_by(UserMonthlyStats.productivity_score.desc())
        )
        all_stats = result.scalars().all()
        
        # Find user's rank
        for rank, stats in enumerate(all_stats, start=1):
            if stats.user_id == user_id:
                return rank
        
        return len(all_stats) + 1  # User not found, return last rank
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get activity summary for a user over the last N days.
        Query raw activity logs directly for real-time data.
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            Dictionary with activity summary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query raw activity logs directly (real-time, no aggregation needed)
        result = await self.session.execute(
            select(UserActivityLog).where(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.timestamp >= start_date,
                    UserActivityLog.timestamp <= end_date,
                    UserActivityLog.status == "success"
                )
            ).order_by(UserActivityLog.timestamp)
        )
        activities = result.scalars().all()
        
        # Count by action type
        action_counts = {}
        for activity in activities:
            action_type = activity.action_type
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        # Aggregate totals
        summary = {
            "period_days": days,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "total_logins": action_counts.get("login", 0),
            "total_resumes_vetted": action_counts.get("vet_resume", 0) + action_counts.get("batch_vet_resumes", 0),
            "total_candidates_viewed": action_counts.get("view_candidate", 0),
            "total_candidates_created": action_counts.get("create_candidate", 0),
            "total_searches": action_counts.get("search_candidates", 0) + action_counts.get("search_jobs", 0),
            "total_jobs_created": action_counts.get("create_job", 0),
            "total_interviews_scheduled": action_counts.get("schedule_interview", 0) + action_counts.get("create_interview", 0),
            "total_session_time_hours": sum(a.duration_ms or 0 for a in activities) / 3600000,  # ms to hours
            "active_days": len(set(a.timestamp.date() for a in activities)),
            "daily_breakdown": []  # Can be populated if needed
        }
        
        logger.info(f"Activity summary for user {user_id}: {len(activities)} activities, {summary['total_resumes_vetted']} resumes vetted")
        
        return summary
    
    async def get_team_leaderboard(self, period: str = "month", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get team leaderboard based on productivity scores.
        
        Args:
            period: 'day', 'week', or 'month'
            limit: Number of top users to return
        
        Returns:
            List of user rankings
        """
        today = date.today()
        
        if period == "month":
            result = await self.session.execute(
                select(UserMonthlyStats, User).join(
                    User, UserMonthlyStats.user_id == User.id
                ).where(
                    and_(
                        UserMonthlyStats.year == today.year,
                        UserMonthlyStats.month == today.month
                    )
                ).order_by(UserMonthlyStats.productivity_score.desc()).limit(limit)
            )
            stats_users = result.all()
            
            leaderboard = [
                {
                    "rank": idx + 1,
                    "user_id": stats.user_id,
                    "user_name": user.full_name,
                    "productivity_score": stats.productivity_score,
                    "quality_score": stats.quality_score,
                    "resumes_vetted": stats.resumes_vetted,
                    "candidates_created": stats.candidates_created,
                    "interviews_scheduled": stats.interviews_scheduled
                }
                for idx, (stats, user) in enumerate(stats_users)
            ]
        
        # TODO: Implement week and day leaderboards
        
        return leaderboard
