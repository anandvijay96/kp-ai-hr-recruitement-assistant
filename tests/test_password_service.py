"""Unit tests for password service"""
import pytest
from services.password_service import PasswordService


@pytest.fixture
def password_service():
    """Create password service instance with lower cost for faster tests"""
    return PasswordService(cost_factor=4)


def test_hash_password(password_service):
    """Test password hashing"""
    password = "TestPassword123!"
    hashed = password_service.hash_password(password)
    
    assert hashed is not None
    assert hashed != password
    assert hashed.startswith("$2b$")


def test_verify_password_correct(password_service):
    """Test password verification with correct password"""
    password = "TestPassword123!"
    hashed = password_service.hash_password(password)
    
    assert password_service.verify_password(password, hashed) is True


def test_verify_password_incorrect(password_service):
    """Test password verification with incorrect password"""
    password = "TestPassword123!"
    hashed = password_service.hash_password(password)
    
    assert password_service.verify_password("WrongPassword", hashed) is False


def test_check_password_strength_strong(password_service):
    """Test password strength check for strong password"""
    result = password_service.check_password_strength("StrongP@ssw0rd!")
    
    assert result["strength"] == "strong"
    assert result["score"] >= 5


def test_check_password_strength_weak(password_service):
    """Test password strength check for weak password"""
    result = password_service.check_password_strength("password")
    
    assert result["strength"] == "weak"
    assert result["score"] <= 2


def test_validate_password_requirements_valid(password_service):
    """Test password validation with valid password"""
    is_valid, errors = password_service.validate_password_requirements("ValidP@ss123")
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_password_requirements_too_short(password_service):
    """Test password validation with too short password"""
    is_valid, errors = password_service.validate_password_requirements("Short1!")
    
    assert is_valid is False
    assert any("8 characters" in error for error in errors)


def test_validate_password_requirements_no_uppercase(password_service):
    """Test password validation without uppercase"""
    is_valid, errors = password_service.validate_password_requirements("password123!")
    
    assert is_valid is False
    assert any("uppercase" in error for error in errors)


def test_check_password_history_found(password_service):
    """Test password history check when password was used"""
    password = "TestPassword123!"
    hashed1 = password_service.hash_password(password)
    hashed2 = password_service.hash_password("OtherPassword456!")
    
    password_hashes = [hashed1, hashed2]
    
    assert password_service.check_password_history(password, password_hashes) is True


def test_check_password_history_not_found(password_service):
    """Test password history check when password was not used"""
    password = "NewPassword789!"
    hashed1 = password_service.hash_password("OldPassword123!")
    hashed2 = password_service.hash_password("OtherPassword456!")
    
    password_hashes = [hashed1, hashed2]
    
    assert password_service.check_password_history(password, password_hashes) is False
