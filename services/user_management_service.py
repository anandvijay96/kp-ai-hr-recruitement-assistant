"""User management service"""
import logging
import secrets
import string
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
import json

from models.database import User, UserSession, UserAuditLog
from models.user_management_schemas import (
    UserCreateRequest, UserUpdateRequest, UserRoleChangeRequest,
    UserDeactivateRequest, UserReactivateRequest
)
from services.permission_service import PermissionService
from services.password_service import PasswordService

logger = logging.getLogger(__name__)


class UserManagementService:
    """Service for managing users"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.permission_service = PermissionService(db_session)
        self.password_service = PasswordService()
    
    async def list_users(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List users with filtering and pagination
        
        Args:
            status: Filter by status
            role: Filter by role
            department: Filter by department
            search: Search by name or email
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
            page: Page number
            limit: Items per page
            
        Returns:
            Dictionary with users, pagination, and summary
        """
        try:
            # Build query
            query = select(User)
            
            # Apply filters
            if status:
                query = query.where(User.status == status)
            if role:
                query = query.where(User.role == role)
            if department:
                query = query.where(User.department == department)
            if search:
                search_term = f"%{search.lower()}%"
                query = query.where(
                    or_(
                        func.lower(User.full_name).like(search_term),
                        func.lower(User.email).like(search_term)
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply sorting
            sort_column = getattr(User, sort_by, User.created_at)
            if sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            users = result.scalars().all()
            
            # Get summary statistics
            summary = await self._get_user_summary()
            
            # Count active sessions for each user
            user_responses = []
            for user in users:
                session_count_result = await self.db.execute(
                    select(func.count()).select_from(UserSession).where(
                        UserSession.user_id == user.id,
                        UserSession.is_active == True
                    )
                )
                session_count = session_count_result.scalar()
                
                user_dict = {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "mobile": user.mobile,
                    "role": user.role,
                    "department": user.department,
                    "status": user.status,
                    "last_login": user.last_login,
                    "last_activity_at": user.last_activity_at,
                    "created_at": user.created_at,
                    "active_sessions": session_count
                }
                user_responses.append(user_dict)
            
            return {
                "users": user_responses,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit
                },
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            raise
    
    async def _get_user_summary(self) -> Dict[str, Any]:
        """Get user summary statistics"""
        try:
            total_result = await self.db.execute(select(func.count()).select_from(User))
            total = total_result.scalar()
            
            active_result = await self.db.execute(
                select(func.count()).select_from(User).where(User.status == "active")
            )
            active = active_result.scalar()
            
            inactive_result = await self.db.execute(
                select(func.count()).select_from(User).where(User.status == "inactive")
            )
            inactive = inactive_result.scalar()
            
            locked_result = await self.db.execute(
                select(func.count()).select_from(User).where(User.status == "locked")
            )
            locked = locked_result.scalar()
            
            # Count by role
            admin_result = await self.db.execute(
                select(func.count()).select_from(User).where(User.role == "admin")
            )
            admin_count = admin_result.scalar()
            
            manager_result = await self.db.execute(
                select(func.count()).select_from(User).where(User.role == "manager")
            )
            manager_count = manager_result.scalar()
            
            recruiter_result = await self.db.execute(
                select(func.count()).select_from(User).where(User.role == "recruiter")
            )
            recruiter_count = recruiter_result.scalar()
            
            return {
                "total_users": total,
                "active": active,
                "inactive": inactive,
                "locked": locked,
                "by_role": {
                    "admin": admin_count,
                    "manager": manager_count,
                    "recruiter": recruiter_count
                }
            }
        except Exception as e:
            logger.error(f"Error getting user summary: {str(e)}")
            return {
                "total_users": 0,
                "active": 0,
                "inactive": 0,
                "locked": 0,
                "by_role": {"admin": 0, "manager": 0, "recruiter": 0}
            }
    
    async def create_user(
        self,
        user_data: UserCreateRequest,
        created_by: User,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            created_by: User creating this user
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with user ID and temporary password
        """
        try:
            # Check if email already exists
            existing_result = await self.db.execute(
                select(User).where(func.lower(User.email) == user_data.email.lower())
            )
            if existing_result.scalar_one_or_none():
                raise ValueError("Email already in use")
            
            # Generate password
            temporary_password = None
            activation_token = None
            
            # Handle both enum and string values for password_option
            password_option = user_data.password_option.value if hasattr(user_data.password_option, 'value') else user_data.password_option
            
            if password_option == "auto_generate":
                temporary_password = self._generate_secure_password()
                password_hash = self.password_service.hash_password(temporary_password)
            else:
                activation_token = secrets.token_urlsafe(32)
                password_hash = None  # Will be set on activation
            
            # Create user
            # Handle both enum and string values
            role_value = user_data.role.value if hasattr(user_data.role, 'value') else user_data.role
            status_value = user_data.status.value if hasattr(user_data.status, 'value') else user_data.status
            
            new_user = User(
                full_name=user_data.full_name,
                email=user_data.email,
                mobile=user_data.mobile,
                role=role_value,
                department=user_data.department,
                password_hash=password_hash,
                status=status_value,
                is_active=True if status_value == "active" else False,
                email_verified=True,  # Auto-verify for now
                created_by=created_by.id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_user)
            await self.db.flush()
            
            # Create audit log
            await self._create_audit_log(
                target_user_id=new_user.id,
                action_type="create",
                new_values={
                    "full_name": new_user.full_name,
                    "email": new_user.email,
                    "role": new_user.role,
                    "department": new_user.department,
                    "status": new_user.status
                },
                performed_by=created_by.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.db.commit()
            
            logger.info(f"User created successfully: {new_user.email}")
            
            return {
                "id": new_user.id,
                "full_name": new_user.full_name,
                "email": new_user.email,
                "role": new_user.role,
                "status": new_user.status,
                "temporary_password": temporary_password,
                "activation_link": f"/activate/{activation_token}" if activation_token else None,
                "message": "User created successfully"
            }
            
        except ValueError as e:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed user information"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            # Get permissions
            permissions = await self.permission_service.get_user_permissions(user_id)
            
            # Get active sessions count
            session_count_result = await self.db.execute(
                select(func.count()).select_from(UserSession).where(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            session_count = session_count_result.scalar()
            
            return {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "mobile": user.mobile,
                "role": user.role,
                "department": user.department,
                "status": user.status,
                "email_verified": user.email_verified,
                "last_login": user.last_login,
                "last_activity_at": user.last_activity_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "failed_login_attempts": user.failed_login_attempts,
                "password_changed_at": user.password_changed_at,
                "permissions": permissions,
                "custom_permissions": [],
                "active_sessions": session_count,
                "statistics": {
                    "jobs_created": 0,  # TODO: Implement
                    "resumes_uploaded": 0,  # TODO: Implement
                    "candidates_hired": 0,  # TODO: Implement
                    "login_count": user.login_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            raise
    
    async def update_user(
        self,
        user_id: str,
        user_data: UserUpdateRequest,
        updated_by: User,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Update user information"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            # Store old values for audit
            old_values = {
                "full_name": user.full_name,
                "mobile": user.mobile,
                "department": user.department
            }
            
            # Update fields
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            if user_data.mobile is not None:
                user.mobile = user_data.mobile
            if user_data.department is not None:
                user.department = user_data.department
            
            user.updated_at = datetime.utcnow()
            
            # Create audit log
            await self._create_audit_log(
                target_user_id=user_id,
                action_type="update",
                old_values=old_values,
                new_values={
                    "full_name": user.full_name,
                    "mobile": user.mobile,
                    "department": user.department
                },
                performed_by=updated_by.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.db.commit()
            
            logger.info(f"User updated successfully: {user.email}")
            
            return {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "mobile": user.mobile,
                "role": user.role,
                "department": user.department,
                "updated_at": user.updated_at,
                "message": "User updated successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            raise
    
    async def change_user_role(
        self,
        user_id: str,
        role_data: UserRoleChangeRequest,
        changed_by: User,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Change user role"""
        try:
            # Validate role change
            is_valid, error_msg = await self.permission_service.validate_role_change(
                user_id, role_data.new_role.value
            )
            if not is_valid:
                raise ValueError(error_msg)
            
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            old_role = user.role
            user.role = role_data.new_role.value
            user.updated_at = datetime.utcnow()
            
            # Create audit log
            await self._create_audit_log(
                target_user_id=user_id,
                action_type="role_change",
                old_values={"role": old_role},
                new_values={"role": user.role, "reason": role_data.reason},
                performed_by=changed_by.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.db.commit()
            
            logger.info(f"User role changed: {user.email} from {old_role} to {user.role}")
            
            return {
                "id": user.id,
                "old_role": old_role,
                "new_role": user.role,
                "effective_at": user.updated_at,
                "message": "Role changed successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error changing user role: {str(e)}")
            raise
    
    async def deactivate_user(
        self,
        user_id: str,
        data: UserDeactivateRequest,
        deactivated_by: User,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Deactivate user account"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            # Check if last admin
            if user.role == "admin":
                admin_count_result = await self.db.execute(
                    select(func.count()).select_from(User).where(
                        User.role == "admin",
                        User.status == "active"
                    )
                )
                if admin_count_result.scalar() <= 1:
                    raise ValueError("Cannot deactivate last active admin")
            
            user.status = "inactive"
            user.is_active = False
            user.deactivated_at = datetime.utcnow()
            user.deactivation_reason = f"{data.reason.value}: {data.reason_details}"
            user.deactivated_by = deactivated_by.id
            
            # Terminate all sessions
            await self.db.execute(
                update(UserSession)
                .where(UserSession.user_id == user_id)
                .values(is_active=False)
            )
            
            # Create audit log
            await self._create_audit_log(
                target_user_id=user_id,
                action_type="deactivate",
                new_values={
                    "status": "inactive",
                    "reason": user.deactivation_reason
                },
                performed_by=deactivated_by.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.db.commit()
            
            logger.info(f"User deactivated: {user.email}")
            
            return {
                "id": user.id,
                "status": user.status,
                "deactivated_at": user.deactivated_at,
                "reason": user.deactivation_reason,
                "sessions_terminated": "all",
                "message": "User deactivated successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deactivating user: {str(e)}")
            raise
    
    async def reactivate_user(
        self,
        user_id: str,
        data: UserReactivateRequest,
        reactivated_by: User,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Reactivate user account"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            user.status = "active"
            user.is_active = True
            user.deactivated_at = None
            user.deactivation_reason = None
            user.deactivated_by = None
            
            # Create audit log
            await self._create_audit_log(
                target_user_id=user_id,
                action_type="reactivate",
                new_values={"status": "active"},
                performed_by=reactivated_by.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.db.commit()
            
            logger.info(f"User reactivated: {user.email}")
            
            return {
                "id": user.id,
                "status": user.status,
                "reactivated_at": datetime.utcnow(),
                "password_reset_required": data.reset_password,
                "message": "User reactivated successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error reactivating user: {str(e)}")
            raise
    
    async def _create_audit_log(
        self,
        target_user_id: str,
        action_type: str,
        performed_by: str,
        old_values: Dict = None,
        new_values: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Create audit log entry"""
        try:
            # Generate checksum
            checksum_data = f"{target_user_id}{action_type}{performed_by}{datetime.utcnow().isoformat()}"
            checksum = hashlib.sha256(checksum_data.encode()).hexdigest()
            
            audit_log = UserAuditLog(
                target_user_id=target_user_id,
                action_type=action_type,
                old_values=old_values,
                new_values=new_values,
                performed_by=performed_by,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                checksum=checksum
            )
            
            self.db.add(audit_log)
            
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
    
    def _generate_secure_password(self, length: int = 12) -> str:
        """Generate secure random password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        # Ensure password has at least one of each type
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        if not any(c in "!@#$%^&*" for c in password):
            password = password[:-1] + secrets.choice("!@#$%^&*")
        
        return password
