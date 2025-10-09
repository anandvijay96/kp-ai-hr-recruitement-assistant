"""User management API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from models.user_management_schemas import (
    UserCreateRequest, UserUpdateRequest, UserRoleChangeRequest,
    UserDeactivateRequest, UserReactivateRequest,
    UserListResponse, UserDetailResponse, UserCreateResponse
)
from services.user_management_service import UserManagementService
from services.permission_service import PermissionService
from services.auth_service import AuthService
from models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["User Management"])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # Get token from header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    
    # TODO: Implement token validation
    # For now, return a mock user (replace with actual implementation)
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


def require_permission(permission: str):
    """Dependency to check if user has required permission"""
    async def check_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        perm_service = PermissionService(db)
        has_perm = await perm_service.has_permission(current_user.id, permission)
        
        if not has_perm:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        
        return current_user
    
    return check_permission


# API Endpoints

@router.get("", response_model=UserListResponse)
async def list_users(
    status: Optional[str] = None,
    role: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|last_login|full_name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage"))
):
    """
    List all users with filtering, sorting, and pagination
    
    Requires: user.manage permission
    """
    try:
        service = UserManagementService(db)
        result = await service.list_users(
            status=status,
            role=role,
            department=department,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage"))
):
    """
    Create a new user account
    
    Requires: user.manage permission
    """
    try:
        service = UserManagementService(db)
        result = await service.create_user(
            user_data=user_data,
            created_by=current_user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed user information
    
    Accessible by: admin or self
    """
    try:
        # Check permission: admin or self
        perm_service = PermissionService(db)
        has_manage_perm = await perm_service.has_permission(current_user.id, "user.manage")
        
        if not has_manage_perm and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        service = UserManagementService(db)
        result = await service.get_user_details(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user information
    
    Accessible by: admin or self (limited fields)
    """
    try:
        # Check permission
        perm_service = PermissionService(db)
        has_manage_perm = await perm_service.has_permission(current_user.id, "user.manage")
        
        if current_user.id == user_id:
            # Users can only update their own name and mobile
            if user_data.department is not None and not has_manage_perm:
                raise HTTPException(status_code=403, detail="Cannot change own department")
        elif not has_manage_perm:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        service = UserManagementService(db)
        result = await service.update_user(
            user_id=user_id,
            user_data=user_data,
            updated_by=current_user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/role")
async def change_user_role(
    user_id: str,
    role_data: UserRoleChangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage"))
):
    """
    Change user role
    
    Requires: user.manage permission
    """
    try:
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        
        service = UserManagementService(db)
        result = await service.change_user_role(
            user_id=user_id,
            role_data=role_data,
            changed_by=current_user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing user role: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    data: UserDeactivateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage"))
):
    """
    Deactivate a user account
    
    Requires: user.manage permission
    """
    try:
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        
        service = UserManagementService(db)
        result = await service.deactivate_user(
            user_id=user_id,
            data=data,
            deactivated_by=current_user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    data: UserReactivateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage"))
):
    """
    Reactivate a deactivated user account
    
    Requires: user.manage permission
    """
    try:
        service = UserManagementService(db)
        result = await service.reactivate_user(
            user_id=user_id,
            data=data,
            reactivated_by=current_user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permissions/matrix")
async def get_permission_matrix(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the complete permission matrix for all roles
    
    Accessible by: any authenticated user
    """
    try:
        perm_service = PermissionService(db)
        result = await perm_service.get_permission_matrix()
        return result
    except Exception as e:
        logger.error(f"Error getting permission matrix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
