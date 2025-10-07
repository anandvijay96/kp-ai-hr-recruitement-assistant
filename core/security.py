"""
Security utilities: encryption, JWT tokens, password hashing
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Encryption for API keys/tokens
ENCRYPTION_KEY = settings.encryption_key


class CredentialEncryption:
    """Encrypt and decrypt API credentials"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        key = encryption_key or ENCRYPTION_KEY
        if not key:
            raise ValueError("Encryption key not configured")
        
        # Ensure key is bytes
        if isinstance(key, str):
            # If it's a base64-encoded key, use it directly
            # Otherwise, generate a key from the string
            try:
                self.fernet = Fernet(key.encode())
            except:
                # Generate a key from the string
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                from cryptography.hazmat.backends import default_backend
                import base64
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'hr_assistant_salt',  # In production, use a random salt
                    iterations=100000,
                    backend=default_backend()
                )
                key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))
                self.fernet = Fernet(key_bytes)
        else:
            self.fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string"""
        if not plaintext:
            return ""
        return self.fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string"""
        if not ciphertext:
            return ""
        return self.fernet.decrypt(ciphertext.encode()).decode()


# Password hashing functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key"""
    return Fernet.generate_key().decode()


# Initialize encryption helper
try:
    credential_encryptor = CredentialEncryption()
except Exception as e:
    logger.warning(f"Credential encryption not available: {e}")
    credential_encryptor = None
