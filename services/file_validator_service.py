"""File validation service for resume uploads"""
import hashlib
import os
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


class FileValidatorService:
    """Service for validating uploaded files"""
    
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    MIME_TYPES = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain'
    }
    
    def validate_file(self, file_content: bytes, file_name: str) -> Tuple[bool, List[str]]:
        """
        Validate file content and name
        
        Args:
            file_content: File binary content
            file_name: Original file name
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate file size
        if len(file_content) == 0:
            errors.append("File is empty")
        elif len(file_content) > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            actual_mb = len(file_content) / (1024 * 1024)
            errors.append(f"File size ({actual_mb:.1f}MB) exceeds maximum limit of {max_mb:.0f}MB")
        
        # Validate file extension
        file_ext = self.get_file_extension(file_name)
        if file_ext not in self.ALLOWED_EXTENSIONS:
            errors.append(f"Invalid file format. Allowed formats: {', '.join(self.ALLOWED_EXTENSIONS)}")
        
        # Note: Removed null byte check as PDF files legitimately contain null bytes
        
        return (len(errors) == 0, errors)
    
    def get_file_extension(self, file_name: str) -> str:
        """
        Extract file extension
        
        Args:
            file_name: File name
            
        Returns:
            File extension with dot (e.g., '.pdf')
        """
        return os.path.splitext(file_name)[1].lower()
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """
        Calculate SHA-256 hash of file for duplicate detection
        
        Args:
            file_content: File binary content
            
        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def get_mime_type(self, file_content: bytes, file_extension: str) -> str:
        """
        Get MIME type based on file extension
        
        Args:
            file_content: File binary content (for future magic byte detection)
            file_extension: File extension without dot
            
        Returns:
            MIME type string
        """
        # For now, use extension-based detection
        # In production, use python-magic for actual content detection
        return self.MIME_TYPES.get(file_extension, "application/octet-stream")
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        dangerous_chars = ['..', '/', '\\', '\x00', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def validate_password_requirements(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password meets requirements
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        # Check byte length for bcrypt compatibility
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            errors.append("Password is too long (max 72 bytes)")
        
        return (len(errors) == 0, errors)
