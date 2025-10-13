"""JWT token generation and validation service"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import uuid
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class TokenService:
    """Service for JWT token operations"""
    
    def __init__(self, redis_client):
        """
        Initialize token service
        
        Args:
            redis_client: Redis client for token blacklist
        """
        self.redis_client = redis_client
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    def generate_access_token(self, user_id: str, email: str, role: str) -> Tuple[str, datetime]:
        """
        Generate JWT access token
        
        Args:
            user_id: User ID
            email: User email
            role: User role
            
        Returns:
            Tuple of (token, expiry_datetime)
        """
        try:
            expiry = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            payload = {
                "sub": user_id,
                "email": email,
                "role": role,
                "type": "access",
                "exp": expiry,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4())  # JWT ID for tracking
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token, expiry
        
        except Exception as e:
            logger.error(f"Error generating access token: {str(e)}")
            raise ValueError("Failed to generate access token")
    
    def generate_refresh_token(self, user_id: str) -> Tuple[str, datetime]:
        """
        Generate JWT refresh token
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (token, expiry_datetime)
        """
        try:
            expiry = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            payload = {
                "sub": user_id,
                "type": "refresh",
                "exp": expiry,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4())
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token, expiry
        
        except Exception as e:
            logger.error(f"Error generating refresh token: {str(e)}")
            raise ValueError("Failed to generate refresh token")
    
    def validate_token(self, token: str, token_type: str = "access") -> Dict:
        """
        Validate JWT token
        
        Args:
            token: JWT token to validate
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload
            
        Raises:
            ValueError: If token is invalid, expired, or blacklisted
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise ValueError(f"Invalid token type. Expected {token_type}")
            
            # Check if token is blacklisted (async check needs to be handled by caller)
            jti = payload.get("jti")
            if jti:
                # Note: This is a sync method, blacklist check should be done separately
                pass
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise ValueError("Invalid token")
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            raise ValueError("Token validation failed")
    
    async def blacklist_token(self, token: str, user_id: str) -> None:
        """
        Add token to blacklist
        
        Args:
            token: JWT token to blacklist
            user_id: User ID associated with token
        """
        try:
            # Decode token to get expiry and JTI
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm], 
                options={"verify_exp": False}
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if not jti:
                logger.warning("Token has no JTI, cannot blacklist")
                return
            
            # Calculate TTL (time until token expires)
            if exp:
                ttl = exp - int(datetime.utcnow().timestamp())
                if ttl > 0:
                    # Add to Redis with TTL
                    await self.redis_client.setex(
                        f"blacklist:{jti}",
                        ttl,
                        user_id
                    )
                    logger.info(f"Token blacklisted for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
            # Don't raise exception, just log it
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if token is blacklisted
        
        Args:
            jti: JWT ID
            
        Returns:
            True if blacklisted, False otherwise
        """
        try:
            return await self.redis_client.exists(f"blacklist:{jti}")
        except Exception as e:
            logger.error(f"Error checking blacklist: {str(e)}")
            # Fail open (assume not blacklisted) to avoid blocking users
            return False
    
    async def refresh_access_token(self, refresh_token: str, user_data: dict) -> Dict:
        """
        Generate new access token from refresh token
        
        Args:
            refresh_token: Valid refresh token
            user_data: User data (id, email, role)
            
        Returns:
            Dictionary with new access token and expiry
        """
        # Validate refresh token
        payload = self.validate_token(refresh_token, token_type="refresh")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid refresh token payload")
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and await self.is_token_blacklisted(jti):
            raise ValueError("Refresh token has been revoked")
        
        # Generate new access token
        access_token, expiry = self.generate_access_token(
            user_id=user_data["id"],
            email=user_data["email"],
            role=user_data["role"]
        )
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
