"""
Authentication and authorization middleware
Provides decorators and utilities for protecting routes
"""
from functools import wraps
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Get current user from session
    
    Returns:
        User dict if authenticated, None otherwise
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    # For MVP, return basic user info from session
    # In production, fetch from database
    return {
        "id": user_id,
        "email": request.session.get("user_email", "user@example.com"),
        "name": request.session.get("user_name", "HR Manager"),
        "role": request.session.get("user_role", "recruiter")
    }


def require_auth(func):
    """
    Decorator to require authentication for page routes
    Redirects to login if not authenticated
    
    Usage:
        @app.get("/dashboard")
        @require_auth
        async def dashboard(request: Request):
            user = await get_current_user(request)
            return templates.TemplateResponse(...)
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_current_user(request)
        if not user:
            logger.info(f"Unauthenticated access attempt to {request.url.path}")
            return RedirectResponse(url=f"/login?next={request.url.path}", status_code=302)
        return await func(request, *args, **kwargs)
    return wrapper


async def get_current_user_or_redirect(request: Request):
    """
    Dependency for getting current user or redirecting to login
    Use with FastAPI Depends()
    
    Usage:
        @app.get("/api/data")
        async def get_data(user = Depends(get_current_user_or_redirect)):
            return {"user": user}
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def check_permission(user: dict, permission: str) -> bool:
    """
    Check if user has specific permission
    
    Permissions by role:
    - admin: all permissions
    - recruiter: view_candidates, vet_resumes, manage_jobs, create_jobs
    - hr_manager: view_candidates, view_jobs, view_reports
    - viewer: view_candidates
    
    Args:
        user: User dict with 'role' key
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    ROLE_PERMISSIONS = {
        "admin": ["all"],
        "recruiter": [
            "view_candidates",
            "edit_candidates",
            "vet_resumes",
            "manage_jobs",
            "create_jobs",
            "view_reports"
        ],
        "hr_manager": [
            "view_candidates",
            "view_jobs",
            "view_reports"
        ],
        "viewer": [
            "view_candidates",
            "view_jobs"
        ]
    }
    
    user_role = user.get("role", "viewer")
    user_permissions = ROLE_PERMISSIONS.get(user_role, [])
    
    # Admin has all permissions
    if "all" in user_permissions:
        return True
    
    return permission in user_permissions


def require_permission(permission: str):
    """
    Decorator to require specific permission
    
    Usage:
        @app.get("/admin")
        @require_permission("admin")
        async def admin_page(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)
            
            if not check_permission(user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
