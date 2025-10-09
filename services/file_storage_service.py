"""File storage service for managing resume uploads"""
import os
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        self.base_upload_dir = getattr(settings, 'resume_upload_dir', 'uploads/resumes')
        self.ensure_upload_directory()
    
    def ensure_upload_directory(self):
        """Create upload directory if it doesn't exist"""
        try:
            Path(self.base_upload_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Upload directory ensured: {self.base_upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory: {str(e)}")
            raise
    
    def generate_file_path(self, user_id: str, resume_id: str, file_extension: str) -> str:
        """
        Generate organized file path
        
        Structure: uploads/resumes/{year}/{month}/{user_id}/{resume_id}.{ext}
        
        Args:
            user_id: User ID who uploaded the file
            resume_id: Unique resume ID
            file_extension: File extension (without dot)
            
        Returns:
            Relative file path
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        # Create directory structure
        dir_path = os.path.join(
            self.base_upload_dir,
            year,
            month,
            user_id
        )
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Generate file path
        file_name = f"{resume_id}.{file_extension}"
        return os.path.join(dir_path, file_name)
    
    async def save_file(self, file_content: bytes, file_path: str) -> bool:
        """
        Save file to storage
        
        Args:
            file_content: File binary content
            file_path: Destination file path
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If file save fails
        """
        try:
            # Ensure directory exists
            Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"File saved successfully: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving file to {file_path}: {str(e)}")
            raise ValueError(f"Failed to save file: {str(e)}")
    
    async def read_file(self, file_path: str) -> bytes:
        """
        Read file from storage
        
        Args:
            file_path: File path to read
            
        Returns:
            File content as bytes
            
        Raises:
            ValueError: If file not found or read fails
        """
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            return content
        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise ValueError("File not found")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise ValueError(f"Failed to read file: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage
        
        Args:
            file_path: File path to delete
            
        Returns:
            True if deleted, False if file doesn't exist
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    async def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            file_path: File path
            
        Returns:
            File size in bytes
        """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size for {file_path}: {str(e)}")
            return 0
    
    def get_absolute_path(self, relative_path: str) -> str:
        """
        Convert relative path to absolute path
        
        Args:
            relative_path: Relative file path
            
        Returns:
            Absolute file path
        """
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.abspath(relative_path)
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file exists
        """
        return os.path.exists(file_path)
