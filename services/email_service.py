"""Email sending service using SendGrid"""
from typing import Optional
import logging
from core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("sendgrid package not installed. Emails will be logged instead of sent.")


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        """Initialize email service with SendGrid"""
        self.api_key = settings.sendgrid_api_key
        self.sender_email = settings.sender_email
        self.sender_name = settings.sender_name
        self.frontend_url = settings.frontend_url
        
        if SENDGRID_AVAILABLE and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
            if not SENDGRID_AVAILABLE:
                logger.warning("SendGrid not available. Emails will be logged only.")
            elif not self.api_key:
                logger.warning("SendGrid API key not configured. Emails will be logged only.")
    
    async def send_verification_email(self, to_email: str, full_name: str, token: str) -> bool:
        """
        Send email verification email
        
        Args:
            to_email: Recipient email address
            full_name: Recipient full name
            token: Verification token
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            verification_link = f"{self.frontend_url}/verify-email?token={token}"
            
            subject = "Verify Your Email - HR Recruitment System"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Welcome to HR Recruitment System!</h2>
                    
                    <p>Hi {full_name},</p>
                    
                    <p>Thank you for registering with our HR Recruitment System. Please verify your email address to activate your account.</p>
                    
                    <div style="margin: 30px 0;">
                        <a href="{verification_link}" 
                           style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="color: #666; word-break: break-all;">{verification_link}</p>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        This link will expire in 24 hours.<br>
                        If you didn't create an account, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px;">
                        Best regards,<br>
                        HR Recruitment Team
                    </p>
                </div>
            </body>
            </html>
            """
            
            return await self._send_email(to_email, subject, html_content)
        
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False
    
    async def send_password_reset_email(self, to_email: str, full_name: str, token: str) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            full_name: Recipient full name
            token: Password reset token
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            reset_link = f"{self.frontend_url}/reset-password?token={token}"
            
            subject = "Reset Your Password - HR Recruitment System"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Password Reset Request</h2>
                    
                    <p>Hi {full_name},</p>
                    
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <div style="margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="color: #666; word-break: break-all;">{reset_link}</p>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        This link will expire in 1 hour.<br>
                        If you didn't request a password reset, please ignore this email and your password will remain unchanged.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px;">
                        Best regards,<br>
                        HR Recruitment Team
                    </p>
                </div>
            </body>
            </html>
            """
            
            return await self._send_email(to_email, subject, html_content)
        
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    async def send_password_changed_email(self, to_email: str, full_name: str) -> bool:
        """
        Send password changed confirmation email
        
        Args:
            to_email: Recipient email address
            full_name: Recipient full name
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            subject = "Password Changed - HR Recruitment System"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Password Changed Successfully</h2>
                    
                    <p>Hi {full_name},</p>
                    
                    <p>Your password was successfully changed on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S UTC')}.</p>
                    
                    <p style="color: #dc2626; font-weight: bold;">
                        If you didn't make this change, please contact support immediately.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px;">
                        Best regards,<br>
                        HR Recruitment Team
                    </p>
                </div>
            </body>
            </html>
            """
            
            return await self._send_email(to_email, subject, html_content)
        
        except Exception as e:
            logger.error(f"Error sending password changed email: {str(e)}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Internal method to send email via SendGrid
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.client:
                logger.info(f"[DEV MODE] Email to {to_email}: {subject}")
                logger.debug(f"Email content preview: {html_content[:200]}...")
                return True  # Return True in dev mode
            
            message = Mail(
                from_email=Email(self.sender_email, self.sender_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email. Status code: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
