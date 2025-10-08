"""Password hashing, verification, and validation service"""
import bcrypt
import re
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class PasswordService:
    """Service for password operations"""
    
    def __init__(self, cost_factor: int = 12):
        """
        Initialize password service
        
        Args:
            cost_factor: bcrypt cost factor (default: 12, range: 4-31)
        """
        self.cost_factor = cost_factor
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        try:
            if not password:
                raise ValueError("Password cannot be empty")
            
            logger.debug(f"Hashing password with cost factor: {self.cost_factor}")
            password_bytes = password.encode('utf-8')
            
            # Bcrypt has a 72 byte limit, truncate if necessary
            if len(password_bytes) > 72:
                logger.warning(f"Password exceeds 72 bytes ({len(password_bytes)} bytes), truncating")
                password_bytes = password_bytes[:72]
            
            salt = bcrypt.gensalt(rounds=self.cost_factor)
            hashed = bcrypt.hashpw(password_bytes, salt)
            result = hashed.decode('utf-8')
            logger.debug(f"Password hashed successfully, length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Error hashing password: {type(e).__name__}: {str(e)}")
            raise ValueError(f"Failed to hash password: {str(e)}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            password_bytes = plain_password.encode('utf-8')
            
            # Bcrypt has a 72 byte limit, truncate if necessary (same as hashing)
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
    
    def check_password_strength(self, password: str) -> dict:
        """
        Check password strength
        
        Args:
            password: Password to check
            
        Returns:
            Dictionary with strength score and feedback
        """
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        if len(password) >= 12:
            score += 1
        
        # Uppercase check
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Add uppercase letters")
        
        # Lowercase check
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Add lowercase letters")
        
        # Digit check
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Add numbers")
        
        # Special character check
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            score += 1
        else:
            feedback.append("Add special characters")
        
        # Determine strength level
        if score <= 2:
            strength = "weak"
        elif score <= 4:
            strength = "medium"
        else:
            strength = "strong"
        
        return {
            "score": score,
            "max_score": 6,
            "strength": strength,
            "feedback": feedback
        }
    
    def validate_password_requirements(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password meets all requirements
        
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
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append("Password must contain at least one special character")
        
        return (len(errors) == 0, errors)
    
    def check_password_history(self, new_password: str, password_hashes: List[str]) -> bool:
        """
        Check if password was used before
        
        Args:
            new_password: New password to check
            password_hashes: List of previous password hashes
            
        Returns:
            True if password was used before, False otherwise
        """
        for old_hash in password_hashes:
            if self.verify_password(new_password, old_hash):
                return True
        return False
