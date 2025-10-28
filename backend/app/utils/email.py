"""
Email utilities for sending notifications and password reset emails.
"""

from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Email service for sending various types of emails."""
    
    def __init__(self):
        self.sendgrid_client = None
        if settings.sendgrid_api_key:
            self.sendgrid_client = SendGridAPIClient(api_key=settings.sendgrid_api_key)
    
    def send_email(self, to_email: str, subject: str, html_content: str, plain_text_content: str = None) -> bool:
        """Send an email using SendGrid."""
        if not self.sendgrid_client:
            logger.warning("SendGrid API key not configured, email not sent")
            return False
        
        try:
            message = Mail(
                from_email=settings.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content
            )
            
            response = self.sendgrid_client.send(message)
            logger.info(f"Email sent successfully to {to_email}, status: {response.status_code}")
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str, first_name: str) -> bool:
        """Send welcome email to new user."""
        subject = "Welcome to BulkFoodHub!"
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to BulkFoodHub, {first_name}!</h2>
            <p>Thank you for joining our platform. You can now start browsing and purchasing bulk food products.</p>
            <p>If you have any questions, please don't hesitate to contact our support team.</p>
            <p>Best regards,<br>The BulkFoodHub Team</p>
        </body>
        </html>
        """
        
        plain_text_content = f"""
        Welcome to BulkFoodHub, {first_name}!
        
        Thank you for joining our platform. You can now start browsing and purchasing bulk food products.
        
        If you have any questions, please don't hesitate to contact our support team.
        
        Best regards,
        The BulkFoodHub Team
        """
        
        return self.send_email(to_email, subject, html_content, plain_text_content)
    
    def send_password_reset_email(self, to_email: str, reset_token: str, first_name: str) -> bool:
        """Send password reset email."""
        reset_url = f"https://bulkfoodhub.com/reset-password?token={reset_token}"
        
        subject = "Reset Your BulkFoodHub Password"
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {first_name},</p>
            <p>You requested to reset your password. Click the link below to reset it:</p>
            <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>Best regards,<br>The BulkFoodHub Team</p>
        </body>
        </html>
        """
        
        plain_text_content = f"""
        Password Reset Request
        
        Hello {first_name},
        
        You requested to reset your password. Click the link below to reset it:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        The BulkFoodHub Team
        """
        
        return self.send_email(to_email, subject, html_content, plain_text_content)
    
    def send_email_verification(self, to_email: str, verification_token: str, first_name: str) -> bool:
        """Send email verification email."""
        verification_url = f"https://bulkfoodhub.com/verify-email?token={verification_token}"
        
        subject = "Verify Your BulkFoodHub Email"
        html_content = f"""
        <html>
        <body>
            <h2>Email Verification</h2>
            <p>Hello {first_name},</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>Best regards,<br>The BulkFoodHub Team</p>
        </body>
        </html>
        """
        
        plain_text_content = f"""
        Email Verification
        
        Hello {first_name},
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        This link will expire in 24 hours.
        
        Best regards,
        The BulkFoodHub Team
        """
        
        return self.send_email(to_email, subject, html_content, plain_text_content)


# Global email service instance
email_service = EmailService()
