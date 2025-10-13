"""Tests for client management service"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from services.client_management_service import ClientManagementService
from models.database import Client, ClientContact, User
from models.client_schemas import ClientCreateRequest, ClientContactCreate


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Mock user"""
    user = Mock(spec=User)
    user.id = "user-123"
    user.email = "admin@example.com"
    user.role = "admin"
    return user


@pytest.fixture
def client_service(mock_db):
    """Client management service instance"""
    return ClientManagementService(mock_db)


@pytest.mark.asyncio
async def test_generate_client_code(client_service, mock_db):
    """Test client code generation"""
    # Mock the database query to return no existing codes
    mock_db.execute.return_value.scalar.return_value = None
    
    code = await client_service.generate_client_code()
    
    assert code.startswith("CLT-")
    assert len(code.split("-")) == 3
    year = datetime.now().year
    assert str(year) in code


@pytest.mark.asyncio
async def test_generate_client_code_with_existing(client_service, mock_db):
    """Test client code generation with existing codes"""
    year = datetime.now().year
    # Mock existing code
    mock_db.execute.return_value.scalar.return_value = f"CLT-{year}-0005"
    
    code = await client_service.generate_client_code()
    
    assert code == f"CLT-{year}-0006"


@pytest.mark.asyncio
async def test_check_duplicate_client_no_duplicate(client_service, mock_db):
    """Test duplicate check when no duplicate exists"""
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    
    result = await client_service.check_duplicate_client("New Client Corp")
    
    assert result is None


@pytest.mark.asyncio
async def test_check_duplicate_client_found(client_service, mock_db):
    """Test duplicate check when duplicate exists"""
    existing_client = Mock(spec=Client)
    existing_client.id = "client-123"
    existing_client.name = "Existing Client"
    existing_client.client_code = "CLT-2025-0001"
    
    mock_db.execute.return_value.scalar_one_or_none.return_value = existing_client
    
    result = await client_service.check_duplicate_client("Existing Client")
    
    assert result is not None
    assert result["id"] == "client-123"
    assert result["match_type"] == "exact_name"


@pytest.mark.asyncio
async def test_create_client_success(client_service, mock_db, mock_user):
    """Test successful client creation"""
    # Mock duplicate check
    with patch.object(client_service, 'check_duplicate_client', return_value=None):
        with patch.object(client_service, 'generate_client_code', return_value="CLT-2025-0001"):
            contact_data = ClientContactCreate(
                full_name="John Doe",
                email="john@example.com",
                is_primary=True
            )
            
            request_data = ClientCreateRequest(
                name="Test Client",
                industry="Technology",
                website="https://testclient.com",
                city="San Francisco",
                state="CA",
                country="USA",
                account_manager_id="manager-123",
                contacts=[contact_data]
            )
            
            # Mock database operations
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            client = await client_service.create_client(request_data, mock_user)
            
            # Verify client was added
            assert mock_db.add.called
            assert mock_db.commit.called


@pytest.mark.asyncio
async def test_create_client_duplicate_error(client_service, mock_db, mock_user):
    """Test client creation fails with duplicate"""
    duplicate_info = {
        "id": "existing-123",
        "name": "Existing Client",
        "client_code": "CLT-2025-0001",
        "match_type": "exact_name"
    }
    
    with patch.object(client_service, 'check_duplicate_client', return_value=duplicate_info):
        contact_data = ClientContactCreate(
            full_name="John Doe",
            email="john@example.com",
            is_primary=True
        )
        
        request_data = ClientCreateRequest(
            name="Existing Client",
            industry="Technology",
            account_manager_id="manager-123",
            contacts=[contact_data]
        )
        
        with pytest.raises(ValueError, match="already exists"):
            await client_service.create_client(request_data, mock_user)


@pytest.mark.asyncio
async def test_list_clients(client_service, mock_db):
    """Test listing clients with pagination"""
    # Mock clients
    mock_clients = [
        Mock(spec=Client, id="1", name="Client A", status="active"),
        Mock(spec=Client, id="2", name="Client B", status="active"),
    ]
    
    # Mock query results
    mock_db.execute.return_value.scalars.return_value.all.return_value = mock_clients
    mock_db.execute.return_value.scalar.return_value = 2
    
    with patch.object(client_service, '_get_client_summary', return_value={"active": 2}):
        result = await client_service.list_clients(page=1, limit=20)
        
        assert "clients" in result
        assert "pagination" in result
        assert "summary" in result
        assert result["pagination"]["total"] == 2


@pytest.mark.asyncio
async def test_get_client_by_id(client_service, mock_db):
    """Test getting client by ID"""
    mock_client = Mock(spec=Client)
    mock_client.id = "client-123"
    mock_client.name = "Test Client"
    
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_client
    
    result = await client_service.get_client_by_id("client-123")
    
    assert result is not None
    assert result.id == "client-123"


@pytest.mark.asyncio
async def test_deactivate_client(client_service, mock_db, mock_user):
    """Test client deactivation"""
    from models.client_schemas import ClientDeactivateRequest
    
    mock_client = Mock(spec=Client)
    mock_client.id = "client-123"
    mock_client.status = "active"
    
    with patch.object(client_service, 'get_client_by_id', return_value=mock_client):
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        deactivate_data = ClientDeactivateRequest(
            reason="Contract ended",
            reason_details="Client decided to build in-house team"
        )
        
        result = await client_service.deactivate_client("client-123", deactivate_data, mock_user)
        
        assert mock_client.status == "inactive"
        assert mock_client.deactivated_at is not None
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_add_contact(client_service, mock_db):
    """Test adding contact to client"""
    mock_client = Mock(spec=Client)
    mock_client.id = "client-123"
    mock_client.client_code = "CLT-2025-0001"
    
    with patch.object(client_service, 'get_client_by_id', return_value=mock_client):
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        contact_data = ClientContactCreate(
            full_name="Jane Smith",
            email="jane@example.com",
            title="VP of HR",
            is_primary=False
        )
        
        await client_service.add_contact("client-123", contact_data)
        
        assert mock_db.add.called
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_get_account_managers(client_service, mock_db):
    """Test getting list of account managers"""
    mock_managers = [
        Mock(spec=User, id="1", full_name="Manager A", role="manager"),
        Mock(spec=User, id="2", full_name="Admin B", role="admin"),
    ]
    
    mock_db.execute.return_value.scalars.return_value.all.return_value = mock_managers
    
    result = await client_service.get_account_managers()
    
    assert len(result) == 2
    assert result[0].role in ["admin", "manager"]
