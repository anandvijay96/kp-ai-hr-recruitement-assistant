"""Unit tests for permission service"""
import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from services.permission_service import PermissionService
from models.database import User, UserRole, UserPermission


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def permission_service(mock_db_session):
    """Create permission service instance"""
    return PermissionService(mock_db_session)


class TestPermissionService:
    """Test cases for PermissionService"""
    
    @pytest.mark.asyncio
    async def test_get_user_permissions_admin(self, permission_service, mock_db_session):
        """Test getting permissions for admin user"""
        # Arrange
        user_id = "admin-123"
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.role = "admin"
        
        # Mock role
        role = Mock(spec=UserRole)
        role.name = "admin"
        role.permissions = [
            "user.manage", "job.create", "job.edit", "job.delete",
            "resume.upload", "resume.rate", "analytics.view_all"
        ]
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        mock_role_result = AsyncMock()
        mock_role_result.scalar_one_or_none.return_value = role
        
        mock_custom_perms_result = AsyncMock()
        mock_custom_perms_result.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [
            mock_user_result,
            mock_role_result,
            mock_custom_perms_result
        ]
        
        # Act
        permissions = await permission_service.get_user_permissions(user_id)
        
        # Assert
        assert "user.manage" in permissions
        assert "job.create" in permissions
        assert "analytics.view_all" in permissions
        assert len(permissions) == 7
    
    @pytest.mark.asyncio
    async def test_get_user_permissions_with_custom_overrides(self, permission_service, mock_db_session):
        """Test getting permissions with custom overrides"""
        # Arrange
        user_id = "user-123"
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.role = "recruiter"
        
        # Mock role
        role = Mock(spec=UserRole)
        role.name = "recruiter"
        role.permissions = ["resume.upload", "resume.rate"]
        
        # Mock custom permission (grant additional permission)
        custom_perm = Mock(spec=UserPermission)
        custom_perm.permission = "job.create"
        custom_perm.granted = True
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        mock_role_result = AsyncMock()
        mock_role_result.scalar_one_or_none.return_value = role
        
        mock_custom_perms_result = AsyncMock()
        mock_custom_perms_result.scalars.return_value.all.return_value = [custom_perm]
        
        mock_db_session.execute.side_effect = [
            mock_user_result,
            mock_role_result,
            mock_custom_perms_result
        ]
        
        # Act
        permissions = await permission_service.get_user_permissions(user_id)
        
        # Assert
        assert "resume.upload" in permissions
        assert "resume.rate" in permissions
        assert "job.create" in permissions  # Custom permission added
        assert len(permissions) == 3
    
    @pytest.mark.asyncio
    async def test_get_user_permissions_with_revoked_permission(self, permission_service, mock_db_session):
        """Test getting permissions with revoked permission"""
        # Arrange
        user_id = "user-123"
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.role = "manager"
        
        # Mock role
        role = Mock(spec=UserRole)
        role.name = "manager"
        role.permissions = ["job.create", "job.edit", "resume.upload"]
        
        # Mock custom permission (revoke a permission)
        custom_perm = Mock(spec=UserPermission)
        custom_perm.permission = "job.edit"
        custom_perm.granted = False
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        mock_role_result = AsyncMock()
        mock_role_result.scalar_one_or_none.return_value = role
        
        mock_custom_perms_result = AsyncMock()
        mock_custom_perms_result.scalars.return_value.all.return_value = [custom_perm]
        
        mock_db_session.execute.side_effect = [
            mock_user_result,
            mock_role_result,
            mock_custom_perms_result
        ]
        
        # Act
        permissions = await permission_service.get_user_permissions(user_id)
        
        # Assert
        assert "job.create" in permissions
        assert "resume.upload" in permissions
        assert "job.edit" not in permissions  # Revoked
        assert len(permissions) == 2
    
    @pytest.mark.asyncio
    async def test_has_permission_true(self, permission_service, mock_db_session):
        """Test has_permission returns True when user has permission"""
        # Arrange
        user_id = "user-123"
        permission = "job.create"
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.role = "manager"
        
        # Mock role
        role = Mock(spec=UserRole)
        role.permissions = ["job.create", "job.edit"]
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        mock_role_result = AsyncMock()
        mock_role_result.scalar_one_or_none.return_value = role
        
        mock_custom_perms_result = AsyncMock()
        mock_custom_perms_result.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [
            mock_user_result,
            mock_role_result,
            mock_custom_perms_result
        ]
        
        # Act
        has_perm = await permission_service.has_permission(user_id, permission)
        
        # Assert
        assert has_perm is True
    
    @pytest.mark.asyncio
    async def test_has_permission_false(self, permission_service, mock_db_session):
        """Test has_permission returns False when user lacks permission"""
        # Arrange
        user_id = "user-123"
        permission = "user.manage"
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.role = "recruiter"
        
        # Mock role
        role = Mock(spec=UserRole)
        role.permissions = ["resume.upload", "resume.rate"]
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        mock_role_result = AsyncMock()
        mock_role_result.scalar_one_or_none.return_value = role
        
        mock_custom_perms_result = AsyncMock()
        mock_custom_perms_result.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [
            mock_user_result,
            mock_role_result,
            mock_custom_perms_result
        ]
        
        # Act
        has_perm = await permission_service.has_permission(user_id, permission)
        
        # Assert
        assert has_perm is False
    
    @pytest.mark.asyncio
    async def test_validate_role_change_success(self, permission_service, mock_db_session):
        """Test successful role change validation"""
        # Arrange
        user_id = "user-123"
        new_role = "manager"
        
        # Mock user (not admin)
        user = Mock(spec=User)
        user.id = user_id
        user.role = "recruiter"
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result
        
        # Act
        is_valid, error_msg = await permission_service.validate_role_change(user_id, new_role)
        
        # Assert
        assert is_valid is True
        assert error_msg is None
    
    @pytest.mark.asyncio
    async def test_validate_role_change_last_admin(self, permission_service, mock_db_session):
        """Test role change validation fails for last admin"""
        # Arrange
        user_id = "admin-123"
        new_role = "manager"
        
        # Mock admin user
        user = Mock(spec=User)
        user.id = user_id
        user.role = "admin"
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        # Mock admin count (only 1 admin)
        mock_admin_list = [user]
        mock_admin_result = AsyncMock()
        mock_admin_result.scalars.return_value.all.return_value = mock_admin_list
        
        mock_db_session.execute.side_effect = [mock_user_result, mock_admin_result]
        
        # Act
        is_valid, error_msg = await permission_service.validate_role_change(user_id, new_role)
        
        # Assert
        assert is_valid is False
        assert "Cannot remove last active admin" in error_msg
    
    @pytest.mark.asyncio
    async def test_get_permission_matrix(self, permission_service, mock_db_session):
        """Test getting permission matrix"""
        # Arrange
        mock_roles = [
            Mock(
                name="admin",
                display_name="HR Admin",
                description="Full system access",
                permissions=["user.manage", "job.create", "job.delete"]
            ),
            Mock(
                name="manager",
                display_name="HR Manager",
                description="Manage jobs and candidates",
                permissions=["job.create", "job.edit", "resume.upload"]
            ),
            Mock(
                name="recruiter",
                display_name="Recruiter",
                description="Upload and rate resumes",
                permissions=["resume.upload", "resume.rate"]
            )
        ]
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_roles
        mock_db_session.execute.return_value = mock_result
        
        # Act
        matrix = await permission_service.get_permission_matrix()
        
        # Assert
        assert "roles" in matrix
        assert "all_permissions" in matrix
        assert len(matrix["roles"]) == 3
        assert len(matrix["all_permissions"]) > 0
        
        # Check role data
        admin_role = next(r for r in matrix["roles"] if r["name"] == "admin")
        assert admin_role["display_name"] == "HR Admin"
        assert "user.manage" in admin_role["permissions"]
