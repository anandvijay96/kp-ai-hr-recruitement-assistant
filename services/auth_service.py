"""Main authentication service with business logic"""
from typing import Optional, Dict, List
import uuid
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from models.database import User, PasswordHistory, VerificationToken, UserSession, UserActivityLog
from services.password_service import PasswordService
from services.token_service import TokenService
from services.email_service import EmailService
from core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Main authentication service handling business logic"""
    
    def __init__(
        self,
        db_session: AsyncSession,
        password_service: PasswordService,
        token_service: TokenService,
        email_service: EmailService
    ):
        self.db = db_session
        self.password_service = password_service
        self.token_service = token_service
        self.email_service = email_service
    
    async def register_user(
        self,
        full_name: str,
        email: str,
        mobile: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Dict:
        """
        Register a new user
        
        Args:
            full_name: User's full name
            email: User's email address
            mobile: User's mobile number
            password: User's password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with user_id, email, and email_sent status
            
        Raises:
            ValueError: If email already exists or validation fails
        """
        try:
            # Check if email already exists
            existing_user = await self.db.execute(
                select(User).where(User.email == email)
            )
            if existing_user.scalar_one_or_none():
                raise ValueError("Email already registered")
            
            # Validate password
            is_valid, errors = self.password_service.validate_password_requirements(password)
            if not is_valid:
                raise ValueError("; ".join(errors))
            
            # Hash password
            try:
                logger.info(f"Attempting to hash password for user: {email}")
                password_hash = self.password_service.hash_password(password)
                logger.info(f"Password hashed successfully for user: {email}")
            except Exception as e:
                logger.error(f"Failed to hash password for {email}: {str(e)}")
                raise ValueError(f"Password hashing failed: {str(e)}")
            
            # Create user
            user = User(
                id=str(uuid.uuid4()),
                full_name=full_name,
                email=email,
                mobile=mobile,
                password_hash=password_hash,
                role="recruiter",  # Default role
                is_active=True,  # Auto-activate for now (no email verification)
                email_verified=True  # Auto-verify for now (no email verification)
            )
            
            self.db.add(user)
            await self.db.flush()
            
            # Skip verification token creation for now (email verification disabled)
            # token = str(uuid.uuid4())
            # token_hash = self.password_service.hash_password(token)
            # 
            # verification_token = VerificationToken(
            #     id=str(uuid.uuid4()),
            #     user_id=user.id,
            #     token_hash=token_hash,
            #     token_type="email_verification",
            #     expires_at=datetime.utcnow() + timedelta(hours=24)
            # )
            # 
            # self.db.add(verification_token)
            
            # Log activity
            activity_log = UserActivityLog(
                id=str(uuid.uuid4()),
                user_id=user.id,
                action_type="registration",
                ip_address=ip_address,
                user_agent=user_agent,
                status="success"
            )
            
            self.db.add(activity_log)
            await self.db.commit()
            
            # Email verification disabled - skip sending email
            # email_sent = await self.email_service.send_verification_email(
            #     to_email=email,
            #     full_name=full_name,
            #     token=token
            # )
            
            return {
                "user_id": user.id,
                "email": user.email,
                "email_sent": False  # Email verification disabled
            }
        
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Registration error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Registration failed: {str(e)}")
    
    async def login_user(
        self,
        email: str,
        password: str,
        remember_me: bool,
        ip_address: str,
        user_agent: str
    ) -> Dict:
        """
        Authenticate user and create session
        
        Args:
            email: User email
            password: User password
            remember_me: Keep session active longer
            ip_address: Client IP
            user_agent: Client user agent
            
        Returns:
            Dictionary with user info and tokens
            
        Raises:
            ValueError: If authentication fails
        """
        try:
            # Find user
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Log failed attempt
                await self._log_activity(
                    user_id=None,
                    action_type="login",
                    status="failure",
                    error_message="Invalid credentials",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise ValueError("Invalid email or password")
            
            # Check if account is locked
            if user.account_locked_until and user.account_locked_until > datetime.utcnow():
                raise ValueError(f"Account locked. Try again later.")
            
            # Verify password
            if not self.password_service.verify_password(password, user.password_hash):
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                if user.failed_login_attempts >= settings.account_lockout_attempts:
                    user.account_locked_until = datetime.utcnow() + timedelta(
                        minutes=settings.account_lockout_duration_minutes
                    )
                
                await self.db.commit()
                
                await self._log_activity(
                    user_id=user.id,
                    action_type="login",
                    status="failure",
                    error_message="Invalid password",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                raise ValueError("Invalid email or password")
            
            # Email verification check disabled for now
            # if not user.email_verified:
            #     raise ValueError("Please verify your email address before logging in")
            
            # Reset failed attempts
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.last_login = datetime.utcnow()
            user.login_count += 1
            
            # Generate tokens
            access_token, access_expiry = self.token_service.generate_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role
            )
            
            refresh_token, refresh_expiry = self.token_service.generate_refresh_token(
                user_id=user.id
            )
            
            # Create session
            session = UserSession(
                id=str(uuid.uuid4()),
                user_id=user.id,
                session_token=access_token,
                refresh_token_hash=self.password_service.hash_password(refresh_token),
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=refresh_expiry,
                is_active=True
            )
            
            self.db.add(session)
            
            # Log successful login
            await self._log_activity(
                user_id=user.id,
                action_type="login",
                status="success",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.db.commit()
            
            return {
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "Bearer",
                    "expires_in": 900  # 15 minutes in seconds
                }
            }
        
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Login error: {str(e)}")
            raise ValueError("Login failed")
    
    async def verify_email(self, token: str) -> None:
        """
        Verify user email with token
        
        Args:
            token: Verification token
            
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            # Find valid tokens
            result = await self.db.execute(
                select(VerificationToken).where(
                    and_(
                        VerificationToken.token_type == "email_verification",
                        VerificationToken.used_at.is_(None),
                        VerificationToken.expires_at > datetime.utcnow()
                    )
                )
            )
            
            verification_token = None
            for token_record in result.scalars():
                if self.password_service.verify_password(token, token_record.token_hash):
                    verification_token = token_record
                    break
            
            if not verification_token:
                raise ValueError("Invalid or expired verification token")
            
            # Update user
            await self.db.execute(
                update(User)
                .where(User.id == verification_token.user_id)
                .values(email_verified=True, is_active=True)
            )
            
            # Mark token as used
            verification_token.used_at = datetime.utcnow()
            
            await self.db.commit()
        
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Email verification error: {str(e)}")
            raise ValueError("Email verification failed")
    
    async def request_password_reset(self, email: str, ip_address: str) -> None:
        """
        Request password reset
        
        Args:
            email: User email
            ip_address: Client IP
        """
        try:
            # Find user
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists
                logger.info(f"Password reset requested for non-existent email: {email}")
                return
            
            # Create reset token
            token = str(uuid.uuid4())
            token_hash = self.password_service.hash_password(token)
            
            reset_token = VerificationToken(
                id=str(uuid.uuid4()),
                user_id=user.id,
                token_hash=token_hash,
                token_type="password_reset",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            self.db.add(reset_token)
            
            # Log activity
            await self._log_activity(
                user_id=user.id,
                action_type="password_reset_request",
                status="success",
                ip_address=ip_address
            )
            
            await self.db.commit()
            
            # Send reset email
            await self.email_service.send_password_reset_email(
                to_email=user.email,
                full_name=user.full_name,
                token=token
            )
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Password reset request error: {str(e)}")
            # Don't raise exception to prevent email enumeration
    
    async def reset_password(self, token: str, new_password: str, ip_address: str) -> None:
        """
        Reset password with token
        
        Args:
            token: Reset token
            new_password: New password
            ip_address: Client IP
            
        Raises:
            ValueError: If token invalid or password validation fails
        """
        try:
            # Validate password
            is_valid, errors = self.password_service.validate_password_requirements(new_password)
            if not is_valid:
                raise ValueError("; ".join(errors))
            
            # Find token
            result = await self.db.execute(
                select(VerificationToken).where(
                    and_(
                        VerificationToken.token_type == "password_reset",
                        VerificationToken.used_at.is_(None),
                        VerificationToken.expires_at > datetime.utcnow()
                    )
                )
            )
            
            reset_token = None
            for token_record in result.scalars():
                if self.password_service.verify_password(token, token_record.token_hash):
                    reset_token = token_record
                    break
            
            if not reset_token:
                raise ValueError("Invalid or expired reset token")
            
            # Get user and password history
            user_result = await self.db.execute(
                select(User).where(User.id == reset_token.user_id)
            )
            user = user_result.scalar_one()
            
            history_result = await self.db.execute(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user.id)
                .order_by(PasswordHistory.created_at.desc())
                .limit(settings.password_history_count)
            )
            password_history = [h.password_hash for h in history_result.scalars()]
            
            # Check password history
            if self.password_service.check_password_history(new_password, password_history):
                raise ValueError("Password was used recently. Please choose a different password")
            
            # Hash new password
            new_password_hash = self.password_service.hash_password(new_password)
            
            # Update user password
            user.password_hash = new_password_hash
            user.password_changed_at = datetime.utcnow()
            
            # Add to password history
            password_history_entry = PasswordHistory(
                id=str(uuid.uuid4()),
                user_id=user.id,
                password_hash=new_password_hash
            )
            self.db.add(password_history_entry)
            
            # Mark token as used
            reset_token.used_at = datetime.utcnow()
            
            # Log activity
            await self._log_activity(
                user_id=user.id,
                action_type="password_reset",
                status="success",
                ip_address=ip_address
            )
            
            await self.db.commit()
            
            # Send confirmation email
            await self.email_service.send_password_changed_email(
                to_email=user.email,
                full_name=user.full_name
            )
        
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Password reset error: {str(e)}")
            raise ValueError("Password reset failed")
    
    async def update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        mobile: Optional[str] = None
    ) -> Dict:
        """Update user profile"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            if full_name:
                user.full_name = full_name
            if mobile:
                user.mobile = mobile
            
            await self.db.commit()
            
            return {
                "id": user.id,
                "full_name": user.full_name,
                "mobile": user.mobile
            }
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Update profile error: {str(e)}")
            raise ValueError("Profile update failed")
    
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> None:
        """Change user password"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            # Verify current password
            if not self.password_service.verify_password(current_password, user.password_hash):
                raise ValueError("Current password is incorrect")
            
            # Validate new password
            is_valid, errors = self.password_service.validate_password_requirements(new_password)
            if not is_valid:
                raise ValueError("; ".join(errors))
            
            # Check password history
            history_result = await self.db.execute(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user.id)
                .order_by(PasswordHistory.created_at.desc())
                .limit(settings.password_history_count)
            )
            password_history = [h.password_hash for h in history_result.scalars()]
            
            if self.password_service.check_password_history(new_password, password_history):
                raise ValueError("Password was used recently")
            
            # Update password
            new_password_hash = self.password_service.hash_password(new_password)
            user.password_hash = new_password_hash
            user.password_changed_at = datetime.utcnow()
            
            # Add to history
            password_history_entry = PasswordHistory(
                id=str(uuid.uuid4()),
                user_id=user.id,
                password_hash=new_password_hash
            )
            self.db.add(password_history_entry)
            
            await self.db.commit()
            
            # Send confirmation email
            await self.email_service.send_password_changed_email(
                to_email=user.email,
                full_name=user.full_name
            )
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Change password error: {str(e)}")
            raise ValueError("Password change failed")
    
    async def _log_activity(
        self,
        user_id: Optional[str],
        action_type: str,
        status: str,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log user activity"""
        try:
            activity_log = UserActivityLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action_type=action_type,
                status=status,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(activity_log)
            await self.db.flush()
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
