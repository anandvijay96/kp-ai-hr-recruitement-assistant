"""Unit tests for user management service"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_management_service import UserManagementService
from models.user_management_schemas import (
    UserCreateRequest, UserUpdateRequest, UserRoleChangeRequest,
    UserDeactivateRequest, UserRole, UserStatus, DeactivationReason
)
from models.database import User


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_admin_user():
    """Create mock admin user"""
    user = Mock(spec=User)
    user.id = "admin-123"
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.role = "admin"
    user.status = "active"
    return user


@pytest.fixture
def user_service(mock_db_session):
    """Create user management service instance"""
    return UserManagementService(mock_db_session)


class TestUserManagementService:
    """Test cases for UserManagementService"""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_db_session, mock_admin_user):
        """Test successful user creation"""
        # Arrange
        user_data = UserCreateRequest(
            full_name="Test User",
            email="test@example.com",
            mobile="+1234567890",
            role=UserRole.RECRUITER,
            department="Engineering"
        )
        
        # Mock database query to return no existing user
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Act
        result = await user_service.create_user(
            user_data=user_data,
            created_by=mock_admin_user,
            ip_address="127.0.0.1"
        )
        
        # Assert
        assert result["email"] == "test@example.com"
        assert result["role"] == "recruiter"
        assert "temporary_password" in result or "activation_link" in result
        assert result["message"] == "User created successfully"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_db_session, mock_admin_user):
        """Test user creation with duplicate email"""
        # Arrange
        user_data = UserCreateRequest(
            full_name="Test User",
            email="existing@example.com",
            role=UserRole.RECRUITER
        )
        
        # Mock database query to return existing user
        existing_user = Mock(spec=User)
        existing_user.email = "existing@example.com"
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db_session.execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already in use"):
            await user_service.create_user(
                user_data=user_data,
                created_by=mock_admin_user
            )
        
        mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_user_role_success(self, user_service, mock_db_session, mock_admin_user):
        """Test successful role change"""
        # Arrange
        user_id = "user-123"
        role_data = UserRoleChangeRequest(
            new_role=UserRole.MANAGER,
            reason="Promoted to team lead"
        )
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.email = "user@example.com"
        user.role = "recruiter"
        
        # Mock database queries
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result
        
        # Mock permission service validation
        with patch.object(user_service.permission_service, 'validate_role_change', 
                         return_value=(True, None)):
            # Act
            result = await user_service.change_user_role(
                user_id=user_id,
                role_data=role_data,
                changed_by=mock_admin_user
            )
        
        # Assert
        assert result["old_role"] == "recruiter"
        assert result["new_role"] == "manager"
        assert user.role == "manager"
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_role_cannot_remove_last_admin(self, user_service, mock_db_session, mock_admin_user):
        """Test that last admin cannot be demoted"""
        # Arrange
        user_id = "admin-123"
        role_data = UserRoleChangeRequest(
            new_role=UserRole.RECRUITER,
            reason="Test"
        )
        
        # Mock permission service to return error
        with patch.object(user_service.permission_service, 'validate_role_change',
                         return_value=(False, "Cannot remove last active admin")):
            # Act & Assert
            with pytest.raises(ValueError, match="Cannot remove last active admin"):
                await user_service.change_user_role(
                    user_id=user_id,
                    role_data=role_data,
                    changed_by=mock_admin_user
                )
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, user_service, mock_db_session, mock_admin_user):
        """Test successful user deactivation"""
        # Arrange
        user_id = "user-123"
        data = UserDeactivateRequest(
            reason=DeactivationReason.RESIGNED,
            reason_details="Accepted position at another company"
        )
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.email = "user@example.com"
        user.role = "recruiter"
        user.status = "active"
        
        # Mock database queries
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result
        
        # Act
        result = await user_service.deactivate_user(
            user_id=user_id,
            data=data,
            deactivated_by=mock_admin_user
        )
        
        # Assert
        assert result["status"] == "inactive"
        assert user.status == "inactive"
        assert user.is_active == False
        assert user.deactivation_reason is not None
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_last_admin_fails(self, user_service, mock_db_session, mock_admin_user):
        """Test that last admin cannot be deactivated"""
        # Arrange
        user_id = "admin-123"
        data = UserDeactivateRequest(
            reason=DeactivationReason.RESIGNED,
            reason_details="Test"
        )
        
        # Mock admin user
        user = Mock(spec=User)
        user.id = user_id
        user.role = "admin"
        user.status = "active"
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 1  # Only one admin
        
        mock_db_session.execute.side_effect = [mock_user_result, mock_count_result]
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot deactivate last active admin"):
            await user_service.deactivate_user(
                user_id=user_id,
                data=data,
                deactivated_by=mock_admin_user
            )
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_db_session, mock_admin_user):
        """Test successful user update"""
        # Arrange
        user_id = "user-123"
        user_data = UserUpdateRequest(
            full_name="Updated Name",
            mobile="+9876543210",
            department="Sales"
        )
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.email = "user@example.com"
        user.full_name = "Old Name"
        user.mobile = "+1234567890"
        user.department = "Engineering"
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result
        
        # Act
        result = await user_service.update_user(
            user_id=user_id,
            user_data=user_data,
            updated_by=mock_admin_user
        )
        
        # Assert
        assert user.full_name == "Updated Name"
        assert user.mobile == "+9876543210"
        assert user.department == "Sales"
        assert result["message"] == "User updated successfully"
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_details_success(self, user_service, mock_db_session):
        """Test getting user details"""
        # Arrange
        user_id = "user-123"
        
        # Mock user
        user = Mock(spec=User)
        user.id = user_id
        user.email = "user@example.com"
        user.full_name = "Test User"
        user.role = "recruiter"
        user.status = "active"
        user.email_verified = True
        user.created_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.login_count = 10
        
        # Mock database queries
        mock_user_result = AsyncMock()
        mock_user_result.scalar_one_or_none.return_value = user
        
        mock_session_count = AsyncMock()
        mock_session_count.scalar.return_value = 2
        
        mock_db_session.execute.side_effect = [mock_user_result, mock_session_count]
        
        # Mock permission service
        with patch.object(user_service.permission_service, 'get_user_permissions',
                         return_value=["resume.upload", "resume.rate"]):
            # Act
            result = await user_service.get_user_details(user_id)
        
        # Assert
        assert result["id"] == user_id
        assert result["email"] == "user@example.com"
        assert result["role"] == "recruiter"
        assert result["active_sessions"] == 2
        assert len(result["permissions"]) == 2
    
    @pytest.mark.asyncio
    async def test_list_users_with_filters(self, user_service, mock_db_session):
        """Test listing users with filters"""
        # Arrange
        mock_users = [
            Mock(
                id="user-1",
                full_name="User 1",
                email="user1@example.com",
                role="recruiter",
                status="active",
                department="Engineering",
                mobile="+1234567890",
                last_login=datetime.utcnow(),
                last_activity_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            ),
            Mock(
                id="user-2",
                full_name="User 2",
                email="user2@example.com",
                role="manager",
                status="active",
                department="Sales",
                mobile="+9876543210",
                last_login=datetime.utcnow(),
                last_activity_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
        ]
        
        # Mock database queries
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 2
        
        mock_users_result = AsyncMock()
        mock_users_result.scalars.return_value.all.return_value = mock_users
        
        mock_session_count = AsyncMock()
        mock_session_count.scalar.return_value = 1
        
        # Set up side effects for multiple execute calls
        mock_db_session.execute.side_effect = [
            mock_count_result,  # Total count
            mock_users_result,  # Users query
            mock_count_result,  # Summary total
            mock_count_result,  # Summary active
            mock_count_result,  # Summary inactive
            mock_count_result,  # Summary locked
            mock_count_result,  # Summary admin count
            mock_count_result,  # Summary manager count
            mock_count_result,  # Summary recruiter count
            mock_session_count,  # Session count for user 1
            mock_session_count   # Session count for user 2
        ]
        
        # Act
        result = await user_service.list_users(
            status="active",
            role="recruiter",
            page=1,
            limit=20
        )
        
        # Assert
        assert len(result["users"]) == 2
        assert result["pagination"]["total"] == 2
        assert result["pagination"]["page"] == 1
        assert "summary" in result


class TestPasswordGeneration:
    """Test password generation"""
    
    def test_generate_secure_password(self, user_service):
        """Test secure password generation"""
        password = user_service._generate_secure_password(12)
        
        assert len(password) == 12
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*" for c in password)
    
    def test_generate_password_different_lengths(self, user_service):
        """Test password generation with different lengths"""
        for length in [8, 12, 16, 20]:
            password = user_service._generate_secure_password(length)
            assert len(password) == length
