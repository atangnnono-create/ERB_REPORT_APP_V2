import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from threading import Thread
from queue import Queue
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class EmailConfig:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.ethereal.email")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.app_name = os.getenv("APP_NAME", "Engineering Report Deck")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@engineeringreports.com")
        self.timeout = int(os.getenv("SMTP_TIMEOUT", "30"))

    @property
    def is_configured(self) -> bool:
        return all([self.smtp_username, self.smtp_password, self.smtp_server])


class EmailService:
    def __init__(self):
        self.config = EmailConfig()
        self._connection_cache = None

        if not self.config.is_configured:
            logger.warning("Email service not fully configured.")

    def send_email(self, to_email: str, subject: str, html_content: str,
                   text_content: str = None) -> bool:
        """
        Simple email sending without retry decorator
        """
        if not self.config.is_configured:
            logger.warning("Email credentials not configured. Skipping email send.")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.app_name} <{self.config.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Create plain text version
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)

            # HTML version
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(self, to_email: str, verification_token: str, username: str):
        """Send verification email"""
        verification_url = f"{self.config.base_url}/auth/verify-email?token={verification_token}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Verify Your Email</h2>
            <p>Hello {username},</p>
            <p>Please verify your email by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>Or copy this URL: {verification_url}</p>
        </div>
        """

        text_content = f"""
        Verify Your Email

        Hello {username},

        Please verify your email by visiting:
        {verification_url}
        """

        subject = "Verify Your Email - Engineering Report Deck"
        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()


def send_password_reset_email(self, to_email: str, reset_token: str, username: str):
    """Send password reset email"""
    reset_url = f"{self.config.base_url}/auth/reset-password?token={reset_token}"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Password Reset Request</h2>
        <p>Hello {username},</p>
        <p>You requested to reset your password. Click the link below to set a new password:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                Reset Password
            </a>
        </p>
        <p>Or copy this URL to your browser:</p>
        <p style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; word-break: break-all;">
            {reset_url}
        </p>
        <p>This link will expire in 24 hours.</p>
        <p>If you didn't request this reset, please ignore this email.</p>
    </div>
    """

    text_content = f"""
    Password Reset Request

    Hello {username},

    You requested to reset your password. Use the following link to set a new password:

    {reset_url}

    This link will expire in 24 hours.

    If you didn't request this reset, please ignore this email.
    """

    subject = "Password Reset - Engineering Report Deck"
    return self.send_email(to_email, subject, html_content, text_content)

def send_password_changed_email(self, to_email: str, username: str):
    """Send notification that password was changed"""
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Password Changed</h2>
        <p>Hello {username},</p>
        <p>Your password was successfully changed.</p>
        <p>If you didn't make this change, please contact support immediately.</p>
    </div>
    """

    text_content = f"""
    Password Changed

    Hello {username},

    Your password was successfully changed.

    If you didn't make this change, please contact support immediately.
    """

    subject = "Password Changed - Engineering Report Deck"
    return self.send_email(to_email, subject, html_content, text_content)