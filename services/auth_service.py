"""
Authentication and OAuth service
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
import google.auth.exceptions

from models.user import User, UserAPICredential
from core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    credential_encryptor
)
from core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Handle user authentication and OAuth flows"""
    
    def __init__(self):
        self.google_client_id = settings.google_oauth_client_id
        self.google_client_secret = settings.google_oauth_client_secret
        self.redirect_uri = settings.oauth_redirect_uri
    
    def create_user(self, db: Session, email: str, name: Optional[str] = None, 
                   password: Optional[str] = None) -> User:
        """Create a new user"""
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(password) if password else None
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user: {email}")
        return user
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        if not user.hashed_password:
            return None  # OAuth-only user
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_user_token(self, user: User) -> str:
        """Create JWT token for user"""
        access_token_expires = timedelta(minutes=30 * 24 * 60)  # 30 days
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        return access_token
    
    def get_google_oauth_flow(self) -> Flow:
        """Create Google OAuth flow"""
        if not self.google_client_id or not self.google_client_secret:
            raise ValueError("Google OAuth credentials not configured")
        
        # OAuth 2.0 scopes for Custom Search API
        scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
        ]
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=scopes,
            redirect_uri=self.redirect_uri
        )
        
        return flow
    
    def initiate_google_oauth(self) -> Dict[str, str]:
        """Initiate Google OAuth flow and return authorization URL"""
        try:
            flow = self.get_google_oauth_flow()
            authorization_url, state = flow.authorization_url(
                access_type='offline',  # Get refresh token
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen to get refresh token
            )
            
            return {
                'authorization_url': authorization_url,
                'state': state
            }
        except Exception as e:
            logger.error(f"Failed to initiate OAuth: {e}")
            raise
    
    def handle_google_oauth_callback(self, db: Session, code: str, state: str) -> Dict[str, Any]:
        """Handle Google OAuth callback and create/update user"""
        try:
            # Exchange code for tokens
            flow = self.get_google_oauth_flow()
            flow.fetch_token(code=code)
            
            # Get credentials
            credentials = flow.credentials
            
            # Verify and decode ID token to get user info
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                self.google_client_id
            )
            
            # Extract user information
            email = id_info.get('email')
            name = id_info.get('name')
            
            if not email:
                raise ValueError("Email not provided by Google")
            
            # Get or create user
            user = self.get_user_by_email(db, email)
            if not user:
                user = self.create_user(db, email=email, name=name)
                logger.info(f"Created new user from OAuth: {email}")
            
            # Store OAuth credentials
            self._store_google_credentials(
                db, 
                user.id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expires_at=credentials.expiry,
                scopes=credentials.scopes
            )
            
            # Create JWT token for our app
            jwt_token = self.create_user_token(user)
            
            return {
                'user': user,
                'token': jwt_token,
                'email': email,
                'name': name
            }
            
        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            raise
    
    def _store_google_credentials(self, db: Session, user_id: str, 
                                  access_token: str, refresh_token: Optional[str],
                                  expires_at: datetime, scopes: list):
        """Store Google OAuth credentials for user"""
        # Check if credentials already exist
        existing = db.query(UserAPICredential).filter(
            UserAPICredential.user_id == user_id,
            UserAPICredential.service_type == 'google_search'
        ).first()
        
        # Encrypt tokens
        encrypted_access = credential_encryptor.encrypt(access_token) if credential_encryptor else access_token
        encrypted_refresh = credential_encryptor.encrypt(refresh_token) if credential_encryptor and refresh_token else None
        
        if existing:
            # Update existing credentials
            existing.oauth_access_token = encrypted_access
            if refresh_token:
                existing.oauth_refresh_token = encrypted_refresh
            existing.oauth_expires_at = expires_at
            existing.oauth_scope = ','.join(scopes) if scopes else None
            existing.updated_at = datetime.utcnow()
            logger.info(f"Updated OAuth credentials for user {user_id}")
        else:
            # Create new credentials
            credential = UserAPICredential(
                user_id=user_id,
                service_type='google_search',
                oauth_access_token=encrypted_access,
                oauth_refresh_token=encrypted_refresh,
                oauth_expires_at=expires_at,
                oauth_scope=','.join(scopes) if scopes else None
            )
            db.add(credential)
            logger.info(f"Created new OAuth credentials for user {user_id}")
        
        db.commit()
    
    def add_manual_api_key(self, db: Session, user_id: str, api_key: str, 
                          engine_id: Optional[str] = None) -> UserAPICredential:
        """Add manual API key for user"""
        # Encrypt API key
        encrypted_key = credential_encryptor.encrypt(api_key) if credential_encryptor else api_key
        
        # Check if credentials already exist
        existing = db.query(UserAPICredential).filter(
            UserAPICredential.user_id == user_id,
            UserAPICredential.service_type == 'google_search'
        ).first()
        
        if existing:
            # Update existing
            existing.api_key = encrypted_key
            existing.api_engine_id = engine_id
            existing.updated_at = datetime.utcnow()
            credential = existing
        else:
            # Create new
            credential = UserAPICredential(
                user_id=user_id,
                service_type='google_search',
                api_key=encrypted_key,
                api_engine_id=engine_id
            )
            db.add(credential)
        
        db.commit()
        db.refresh(credential)
        logger.info(f"Added manual API key for user {user_id}")
        return credential
    
    def remove_credentials(self, db: Session, user_id: str, service_type: str = 'google_search'):
        """Remove API credentials for user"""
        db.query(UserAPICredential).filter(
            UserAPICredential.user_id == user_id,
            UserAPICredential.service_type == service_type
        ).delete()
        db.commit()
        logger.info(f"Removed {service_type} credentials for user {user_id}")
