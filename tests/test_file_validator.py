"""Tests for file validator service"""
import pytest
from services.file_validator_service import FileValidatorService


@pytest.fixture
def validator():
    """Create file validator instance"""
    return FileValidatorService()


def test_validate_pdf_file(validator):
    """Test PDF file validation"""
    # Create a simple PDF-like content (not a real PDF, just for testing)
    pdf_content = b"%PDF-1.4\n" + b"x" * 1000
    
    is_valid, errors = validator.validate_file(pdf_content, "test.pdf")
    assert is_valid == True
    assert len(errors) == 0


def test_validate_empty_file(validator):
    """Test empty file rejection"""
    is_valid, errors = validator.validate_file(b"", "test.pdf")
    assert is_valid == False
    assert any("empty" in error.lower() for error in errors)


def test_validate_oversized_file(validator):
    """Test file size validation"""
    # Create 11MB file
    large_content = b"x" * (11 * 1024 * 1024)
    
    is_valid, errors = validator.validate_file(large_content, "large.pdf")
    assert is_valid == False
    assert any("exceeds maximum limit" in error for error in errors)


def test_validate_invalid_format(validator):
    """Test invalid file format rejection"""
    is_valid, errors = validator.validate_file(b"content", "file.exe")
    assert is_valid == False
    assert any("Invalid file format" in error for error in errors)


def test_get_file_extension(validator):
    """Test file extension extraction"""
    assert validator.get_file_extension("test.pdf") == ".pdf"
    assert validator.get_file_extension("test.PDF") == ".pdf"
    assert validator.get_file_extension("test.docx") == ".docx"
    assert validator.get_file_extension("no_extension") == ""


def test_calculate_file_hash(validator):
    """Test SHA-256 hash calculation"""
    content = b"test content"
    hash1 = validator.calculate_file_hash(content)
    hash2 = validator.calculate_file_hash(content)
    
    # Same content should produce same hash
    assert hash1 == hash2
    # SHA-256 produces 64 hex characters
    assert len(hash1) == 64
    
    # Different content should produce different hash
    different_content = b"different content"
    hash3 = validator.calculate_file_hash(different_content)
    assert hash1 != hash3


def test_sanitize_filename(validator):
    """Test filename sanitization"""
    # Test path traversal prevention
    assert validator.sanitize_filename("../../etc/passwd") == "_.._.._.._etc_passwd"
    
    # Test dangerous characters removal
    assert validator.sanitize_filename("file<>:name.pdf") == "file___name.pdf"
    
    # Test null byte removal
    assert validator.sanitize_filename("file\x00name.pdf") == "file_name.pdf"
    
    # Test normal filename
    assert validator.sanitize_filename("normal_file.pdf") == "normal_file.pdf"


def test_get_mime_type(validator):
    """Test MIME type detection"""
    assert validator.get_mime_type(b"", "pdf") == "application/pdf"
    assert validator.get_mime_type(b"", "docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert validator.get_mime_type(b"", "txt") == "text/plain"
    assert validator.get_mime_type(b"", "unknown") == "application/octet-stream"


def test_validate_file_with_null_bytes(validator):
    """Test file with null bytes is rejected"""
    content_with_nulls = b"\x00\x00\x00" + b"x" * 1000
    is_valid, errors = validator.validate_file(content_with_nulls, "test.pdf")
    assert is_valid == False
    assert any("invalid characters" in error.lower() for error in errors)
