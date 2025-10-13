"""Permission service for role-based access control"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from models.database import User, UserRole, UserPermission

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing user permissions and roles"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for a user (role + custom overrides)
        
        Args:
            user_id: User ID
            
        Returns:
            List of permission strings
        """
        try:
            # Get user
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User not found: {user_id}")
                return []
            
            # Get role permissions
            role_result = await self.db.execute(
                select(UserRole).where(UserRole.name == user.role)
            )
            role = role_result.scalar_one_or_none()
            
            if not role:
                logger.warning(f"Role not found: {user.role}")
                return []
            
            # Parse permissions from JSON
            permissions = role.permissions if isinstance(role.permissions, list) else json.loads(role.permissions or '[]')
            permissions = list(permissions)  # Make a copy
            
            # Get custom permissions
            custom_result = await self.db.execute(
                select(UserPermission).where(UserPermission.user_id == user_id)
            )
            custom_perms = custom_result.scalars().all()
            
            # Apply custom overrides
            for perm in custom_perms:
                if perm.granted and perm.permission not in permissions:
                    permissions.append(perm.permission)
                elif not perm.granted and perm.permission in permissions:
                    permissions.remove(perm.permission)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return []
    
    async def has_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if user has specific permission
        
        Args:
            user_id: User ID
            permission: Permission string
            
        Returns:
            True if user has permission
        """
        permissions = await self.get_user_permissions(user_id)
        return permission in permissions
    
    async def get_permission_matrix(self) -> Dict[str, Any]:
        """
        Get complete permission matrix for all roles
        
        Returns:
            Dictionary with roles and permissions
        """
        try:
            result = await self.db.execute(select(UserRole))
            roles = result.scalars().all()
            
            role_data = []
            all_permissions_set = set()
            
            for role in roles:
                perms = role.permissions if isinstance(role.permissions, list) else json.loads(role.permissions or '[]')
                all_permissions_set.update(perms)
                
                role_data.append({
                    "name": role.name,
                    "display_name": role.display_name,
                    "description": role.description,
                    "permissions": perms
                })
            
            # Define permission metadata
            permission_metadata = {
                "user.manage": {
                    "display_name": "User Management",
                    "description": "Create, edit, and delete users",
                    "category": "Administration"
                },
                "job.create": {
                    "display_name": "Create Jobs",
                    "description": "Create new job postings",
                    "category": "Jobs"
                },
                "job.edit": {
                    "display_name": "Edit Jobs",
                    "description": "Modify existing job postings",
                    "category": "Jobs"
                },
                "job.delete": {
                    "display_name": "Delete Jobs",
                    "description": "Delete job postings",
                    "category": "Jobs"
                },
                "resume.upload": {
                    "display_name": "Upload Resumes",
                    "description": "Upload candidate resumes",
                    "category": "Candidates"
                },
                "resume.rate": {
                    "display_name": "Rate Resumes",
                    "description": "Rate and evaluate resumes",
                    "category": "Candidates"
                },
                "resume.approve": {
                    "display_name": "Approve Ratings",
                    "description": "Approve resume ratings",
                    "category": "Candidates"
                },
                "candidate.hire": {
                    "display_name": "Hire Candidate",
                    "description": "Mark candidates as hired",
                    "category": "Candidates"
                },
                "analytics.view_all": {
                    "display_name": "View All Analytics",
                    "description": "View analytics for all jobs and candidates",
                    "category": "Analytics"
                },
                "analytics.view_own": {
                    "display_name": "View Own Analytics",
                    "description": "View analytics for own activities",
                    "category": "Analytics"
                },
                "settings.manage": {
                    "display_name": "Manage Settings",
                    "description": "Manage system settings",
                    "category": "Administration"
                },
                "audit.view": {
                    "display_name": "View Audit Logs",
                    "description": "View complete audit logs",
                    "category": "Administration"
                },
                "audit.view_readonly": {
                    "display_name": "View Audit Logs (Read-only)",
                    "description": "View audit logs without modification",
                    "category": "Administration"
                },
                "data.export": {
                    "display_name": "Export Data",
                    "description": "Export data to CSV/Excel",
                    "category": "Data"
                }
            }
            
            all_permissions = []
            for perm in sorted(all_permissions_set):
                metadata = permission_metadata.get(perm, {
                    "display_name": perm.replace(".", " ").title(),
                    "description": f"Permission for {perm}",
                    "category": "Other"
                })
                all_permissions.append({
                    "key": perm,
                    **metadata
                })
            
            return {
                "roles": role_data,
                "all_permissions": all_permissions
            }
            
        except Exception as e:
            logger.error(f"Error getting permission matrix: {str(e)}")
            return {"roles": [], "all_permissions": []}
    
    async def validate_role_change(self, user_id: str, new_role: str) -> tuple[bool, Optional[str]]:
        """
        Validate if role change is allowed
        
        Args:
            user_id: User ID
            new_role: New role to assign
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get user
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            # Check if removing last admin
            if user.role == "admin" and new_role != "admin":
                admin_count_result = await self.db.execute(
                    select(User).where(
                        User.role == "admin",
                        User.status == "active"
                    )
                )
                admin_count = len(admin_count_result.scalars().all())
                
                if admin_count <= 1:
                    return False, "Cannot remove last active admin"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating role change: {str(e)}")
            return False, str(e)
