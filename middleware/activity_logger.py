"""
Activity Logging Middleware - Phase 3
======================================
Automatically tracks all user actions with entity-level granularity.

Features:
- Automatic activity logging for all authenticated requests
- Entity extraction from request context
- Performance monitoring (request duration)
- Async database logging
- Error handling and fallback
"""
import time
import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.database import UserActivityLog
import uuid

logger = logging.getLogger(__name__)


class ActivityLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log user activity for all requests.
    
    Tracks:
    - User actions (login, view, create, update, delete)
    - Entity interactions (candidate, job, resume, etc.)
    - Request metadata (method, path, duration)
    - Performance metrics
    """
    
    # Paths to exclude from logging (static files, health checks, etc.)
    EXCLUDED_PATHS = {
        "/static",
        "/favicon.ico",
        "/api/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    # Action type mapping based on HTTP method and path patterns
    ACTION_MAPPING = {
        "GET": {
            "/candidates": "search_candidates",
            "/candidates/": "view_candidate",
            "/jobs": "search_jobs",
            "/jobs/": "view_job",
            "/resumes": "search_resumes",
            "/resumes/": "view_resume",
            "/api/v1/dashboard": "view_dashboard",
            "/api/v1/admin": "view_admin",
        },
        "POST": {
            "/candidates": "create_candidate",
            "/jobs": "create_job",
            "/api/v1/vetting/scan": "vet_resume",
            "/api/scan-resume": "vet_resume",
            "/api/batch-scan": "batch_vet_resumes",
            "/auth/login": "login",
            "/api/auth/login": "login",
        },
        "PUT": {
            "/candidates/": "update_candidate",
            "/jobs/": "update_job",
            "/resumes/": "update_resume",
        },
        "DELETE": {
            "/candidates/": "delete_candidate",
            "/jobs/": "delete_job",
            "/resumes/": "delete_resume",
        }
    }
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log activity"""
        
        # Skip excluded paths
        if self._should_skip_logging(request.url.path):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract user info from request state (set by auth middleware)
        user_id = self._get_user_id(request)
        
        # Process request
        response = None
        error_message = None
        status = "success"
        
        try:
            response = await call_next(request)
            
            # Check if response indicates an error
            if response.status_code >= 400:
                status = "failure"
                error_message = f"HTTP {response.status_code}"
            
        except Exception as e:
            status = "failure"
            error_message = str(e)
            logger.error(f"Error processing request: {e}")
            raise
        
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log activity asynchronously (don't block response)
            if user_id:  # Only log for authenticated users
                try:
                    await self._log_activity(
                        request=request,
                        user_id=user_id,
                        duration_ms=duration_ms,
                        status=status,
                        error_message=error_message
                    )
                except Exception as log_error:
                    # Don't fail the request if logging fails
                    logger.warning(f"Failed to log activity: {log_error}")
        
        return response
    
    def _should_skip_logging(self, path: str) -> bool:
        """Check if path should be excluded from logging"""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request state"""
        try:
            # Check if user is set by auth middleware
            if hasattr(request.state, "user") and request.state.user:
                user = request.state.user
                # Handle both dict and object types
                if isinstance(user, dict):
                    return user.get("id")
                elif hasattr(user, "id"):
                    return user.id
        except Exception as e:
            logger.debug(f"Could not extract user ID: {e}")
        
        return None
    
    def _determine_action_type(self, request: Request) -> str:
        """Determine action type from request method and path"""
        method = request.method
        path = request.url.path
        
        # Get method-specific mappings
        method_mappings = self.ACTION_MAPPING.get(method, {})
        
        # Check for exact matches first
        if path in method_mappings:
            return method_mappings[path]
        
        # Check for pattern matches (paths ending with /)
        for pattern, action in method_mappings.items():
            if pattern.endswith("/") and path.startswith(pattern.rstrip("/")):
                return action
        
        # Default action based on method
        default_actions = {
            "GET": "view",
            "POST": "create",
            "PUT": "update",
            "DELETE": "delete",
            "PATCH": "update"
        }
        
        return default_actions.get(method, "unknown")
    
    def _extract_entity_info(self, request: Request) -> tuple[Optional[str], Optional[str]]:
        """
        Extract entity type and ID from request path.
        
        Returns:
            tuple: (entity_type, entity_id)
        """
        path = request.url.path
        parts = [p for p in path.split("/") if p]
        
        # Common entity patterns
        entity_patterns = {
            "candidates": "candidate",
            "jobs": "job",
            "resumes": "resume",
            "interviews": "interview",
            "users": "user",
            "reports": "report"
        }
        
        entity_type = None
        entity_id = None
        
        # Look for entity type in path
        for i, part in enumerate(parts):
            if part in entity_patterns:
                entity_type = entity_patterns[part]
                # Check if next part is an ID (UUID pattern or numeric)
                if i + 1 < len(parts):
                    potential_id = parts[i + 1]
                    # Simple check: if it's not a known route segment, treat as ID
                    if potential_id not in ["create", "edit", "delete", "list", "search"]:
                        entity_id = potential_id
                break
        
        return entity_type, entity_id
    
    def _extract_request_metadata(self, request: Request) -> Dict[str, Any]:
        """Extract relevant metadata from request"""
        metadata = {}
        
        try:
            # Query parameters
            if request.query_params:
                metadata["query_params"] = dict(request.query_params)
            
            # Path parameters (if available)
            if hasattr(request, "path_params") and request.path_params:
                metadata["path_params"] = dict(request.path_params)
            
            # Referrer
            if "referer" in request.headers:
                metadata["referer"] = request.headers["referer"]
            
            # Client info
            if request.client:
                metadata["client_host"] = request.client.host
        
        except Exception as e:
            logger.debug(f"Error extracting request metadata: {e}")
        
        return metadata
    
    async def _log_activity(
        self,
        request: Request,
        user_id: str,
        duration_ms: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log activity to database"""
        
        # Determine action type
        action_type = self._determine_action_type(request)
        
        # Extract entity information
        entity_type, entity_id = self._extract_entity_info(request)
        
        # Extract request metadata
        request_metadata = self._extract_request_metadata(request)
        
        # Get IP address
        ip_address = None
        if request.client:
            ip_address = request.client.host
        
        # Get user agent
        user_agent = request.headers.get("user-agent")
        
        # Create activity log entry
        activity_log = UserActivityLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            request_metadata=json.dumps(request_metadata) if request_metadata else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request.method,
            request_path=request.url.path,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message
        )
        
        # Save to database
        async with AsyncSessionLocal() as session:
            try:
                session.add(activity_log)
                await session.commit()
                logger.debug(f"Logged activity: {action_type} by user {user_id}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save activity log: {e}")
                raise


# Helper function to add middleware to FastAPI app
def setup_activity_logging(app):
    """
    Add activity logging middleware to FastAPI application.
    
    Usage:
        from middleware.activity_logger import setup_activity_logging
        setup_activity_logging(app)
    """
    app.add_middleware(ActivityLoggerMiddleware)
    logger.info("✓ Activity logging middleware enabled")
