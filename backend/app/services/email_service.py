import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional, Tuple
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailConfig:
    """Configuration for email service with Google SMTP defaults"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8501")
        self.app_name = os.getenv("APP_NAME", "Engineering Report Deck")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username or "noreply@engineeringreports.com")
        self.timeout = int(os.getenv("SMTP_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("SMTP_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("SMTP_RETRY_DELAY", "5"))

    @property
    def is_configured(self) -> bool:
        """Check if all required SMTP credentials are provided"""
        return all([
            self.smtp_username,
            self.smtp_password,
            self.smtp_server
        ])


class EmailService:
    """
    Enhanced email service with Google SMTP support and improved error handling
    """

    def __init__(self):
        self.config = EmailConfig()
        self._last_connection_test = None
        self._connection_working = False

        if not self.config.is_configured:
            logger.warning("Email service not fully configured. Missing SMTP credentials.")

    def _test_connection(self) -> bool:
        """Test SMTP connection to Google servers"""
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.config.smtp_username, self.config.smtp_password)

            self._connection_working = True
            self._last_connection_test = datetime.now()
            logger.info("✅ SMTP connection test successful")
            return True

        except Exception as e:
            self._connection_working = False
            logger.warning(f"❌ SMTP connection test failed: {e}")
            return False

    def _handle_google_smtp_errors(self, error: Exception) -> Tuple[bool, str]:
        """
        Handle Google SMTP specific error codes and provide helpful messages
        """
        error_str = str(error).lower()

        # Authentication errors
        if "authentication failed" in error_str or "invalid login" in error_str:
            return False, "SMTP authentication failed. Check your app password."

        elif "application-specific password required" in error_str:
            return False, "App password required. Enable 2FA and use app password."

        elif "username and password not accepted" in error_str:
            return False, "Google account credentials not accepted."

        # Rate limiting and quota errors
        elif "quota exceeded" in error_str or "exceeded sending limit" in error_str:
            return False, "Daily email sending quota exceeded. Try again tomorrow."

        elif "rate limit exceeded" in error_str:
            return False, "Rate limit exceeded. Please wait before sending more emails."

        # Connection errors
        elif "connection refused" in error_str:
            return False, "SMTP connection refused. Check server/port settings."

        elif "timed out" in error_str:
            return False, "SMTP connection timed out."

        # Security errors
        elif "less secure apps" in error_str:
            return False, "Allow 'less secure apps' or use app password."

        elif "suspicious sign in" in error_str:
            return False, "Google blocked sign-in attempt. Check account security."

        # Generic error
        else:
            return False, f"SMTP error: {error}"

    def _create_email_template(self, title: str, username: str, main_content: str,
                               button_text: str = None, button_url: str = None,
                               footer_note: str = None) -> str:
        """Create professional HTML email template"""

        button_html = ""
        if button_text and button_url:
            button_html = f"""
            <div style="text-align: center; margin: 30px 0;">
                <a href="{button_url}" style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 14px 28px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    display: inline-block;
                    box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.3);
                    transition: all 0.3s ease;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px 0 rgba(102, 126, 234, 0.4)';" 
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px 0 rgba(102, 126, 234, 0.3)';">
                    {button_text}
                </a>
            </div>
            """

        footer_note_html = f"<p style='color: #666; font-size: 14px;'>{footer_note}</p>" if footer_note else ""

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f6f9fc;
            color: #333;
        ">
            <div style="
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            ">
                <!-- Header -->
                <div style="
                    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                    color: white;
                    padding: 30px 40px;
                    text-align: center;
                ">
                    <h1 style="
                        margin: 0;
                        font-size: 28px;
                        font-weight: 700;
                    ">🏭 Engineering Report Deck</h1>
                    <p style="
                        margin: 10px 0 0 0;
                        opacity: 0.9;
                        font-size: 16px;
                    ">AI Revolution Driving Engineering Evolution ✨</p>
                </div>

                <!-- Content -->
                <div style="padding: 40px;">
                    <h2 style="
                        color: #2c3e50;
                        margin-top: 0;
                        font-size: 24px;
                        font-weight: 600;
                    ">{title}</h2>

                    <p style="
                        font-size: 16px;
                        line-height: 1.6;
                        color: #555;
                    ">Hello <strong>{username}</strong>,</p>

                    <div style="
                        font-size: 16px;
                        line-height: 1.6;
                        color: #555;
                    ">
                        {main_content}
                    </div>

                    {button_html}

                    {footer_note_html}

                    <!-- Support Info -->
                    <div style="
                        margin-top: 40px;
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 8px;
                        border-left: 4px solid #3498db;
                    ">
                        <p style="
                            margin: 0;
                            font-size: 14px;
                            color: #666;
                        ">
                            <strong>Need help?</strong> If you have any questions or need assistance, 
                            please don't hesitate to contact our support team.
                        </p>
                    </div>
                </div>

                <!-- Footer -->
                <div style="
                    background-color: #f8f9fa;
                    padding: 20px 40px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                ">
                    <p style="
                        margin: 0;
                        font-size: 14px;
                        color: #6c757d;
                    ">
                        © 2024 Engineering Report Deck. All rights reserved.<br>
                        <span style="font-size: 12px;">
                            This is an automated message, please do not reply to this email.
                        </span>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def send_email(self, to_email: str, subject: str, html_content: str,
                   text_content: str = None) -> Tuple[bool, str]:
        """
        Send email with retry logic and comprehensive error handling
        """
        if not self.config.is_configured:
            error_msg = "Email service not configured. Check SMTP credentials."
            logger.error(error_msg)
            return False, error_msg

        # Test connection if it's been a while or previous test failed
        if (not self._last_connection_test or
                (datetime.now() - self._last_connection_test).total_seconds() > 300 or
                not self._connection_working):
            self._test_connection()

        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['From'] = formataddr((self.config.app_name, self.config.from_email))
                msg['To'] = to_email
                msg['Subject'] = subject
                msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

                # Create plain text version
                if text_content:
                    part1 = MIMEText(text_content, 'plain', 'utf-8')
                    msg.attach(part1)

                # HTML version
                part2 = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(part2)

                # Send email
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port,
                                  timeout=self.config.timeout) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.config.smtp_username, self.config.smtp_password)
                    server.send_message(msg)

                logger.info(f"✅ Email sent successfully to {to_email}")
                self._connection_working = True
                return True, "Email sent successfully"

            except Exception as e:
                last_error = e
                logger.warning(f"❌ Email send attempt {attempt + 1} failed: {str(e)}")

                # Handle Google-specific errors
                success, error_msg = self._handle_google_smtp_errors(e)
                if not success and attempt == self.config.max_retries - 1:
                    return False, error_msg

                # Wait before retry
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))

        # If all retries failed
        self._connection_working = False
        return False, f"Failed to send email after {self.config.max_retries} attempts: {str(last_error)}"

    def send_verification_email(self, to_email: str, verification_token: str, username: str) -> Tuple[bool, str]:
        """Send email verification with professional template"""
        verification_url = f"{self.config.base_url}/auth/?token={verification_token}"

        html_content = self._create_email_template(
            title="Verify Your Email Address",
            username=username,
            main_content="""
            <p>Thank you for registering with <strong>Engineering Report Deck</strong>! 
            To complete your registration and start creating professional engineering reports, 
            please verify your email address by clicking the button below.</p>

            <p>Verification ensures the security of your account and allows us to provide 
            you with the best possible experience.</p>
            """,
            button_text="Verify Email Address",
            button_url=verification_url,
            footer_note="This verification link will expire in 24 hours for security reasons."
        )

        text_content = f"""
        Verify Your Email Address - Engineering Report Deck

        Hello {username},

        Thank you for registering with Engineering Report Deck!

        To complete your registration and start creating professional engineering reports, 
        please verify your email address by visiting:

        {verification_url}

        This verification link will expire in 24 hours for security reasons.

        If you didn't create this account, please ignore this email.

        Best regards,
        The Engineering Report Deck Team
        """

        subject = "🔐 Verify Your Email - Engineering Report Deck"
        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> Tuple[bool, str]:
        """Send password reset email with enhanced template"""
        reset_url = f"{self.config.base_url}/auth/?reset_token={reset_token}"

        html_content = self._create_email_template(
            title="Reset Your Password",
            username=username,
            main_content="""
            <p>We received a request to reset your password for your <strong>Engineering Report Deck</strong> account.</p>

            <p>Click the button below to create a new, secure password. If you didn't request 
            this password reset, you can safely ignore this email - your account remains secure.</p>
            """,
            button_text="Reset Password",
            button_url=reset_url,
            footer_note="This password reset link will expire in 1 hour for security reasons."
        )

        text_content = f"""
        Reset Your Password - Engineering Report Deck

        Hello {username},

        We received a request to reset your password for your Engineering Report Deck account.

        To reset your password, please visit:

        {reset_url}

        This password reset link will expire in 1 hour for security reasons.

        If you didn't request this password reset, please ignore this email - 
        your account remains secure.

        Best regards,
        The Engineering Report Deck Team
        """

        subject = "🔄 Reset Your Password - Engineering Report Deck"
        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_changed_email(self, to_email: str, username: str) -> Tuple[bool, str]:
        """Send password change confirmation email"""
        html_content = self._create_email_template(
            title="Password Changed Successfully",
            username=username,
            main_content="""
            <p>Your password for <strong>Engineering Report Deck</strong> was successfully changed.</p>

            <p>If you made this change, no further action is required. If you didn't change 
            your password, please contact our support team immediately as your account 
            security may be compromised.</p>
            """,
            footer_note="For security reasons, we recommend using a strong, unique password."
        )

        text_content = f"""
        Password Changed - Engineering Report Deck

        Hello {username},

        Your password for Engineering Report Deck was successfully changed.

        If you made this change, no further action is required.

        If you didn't change your password, please contact our support team immediately 
        as your account security may be compromised.

        For security reasons, we recommend using a strong, unique password.

        Best regards,
        The Engineering Report Deck Team
        """

        subject = "✅ Password Changed - Engineering Report Deck"
        return self.send_email(to_email, subject, html_content, text_content)

    def send_welcome_email(self, to_email: str, username: str) -> Tuple[bool, str]:
        """Send welcome email after successful verification"""
        dashboard_url = f"{self.config.base_url}/dashboard"

        html_content = self._create_email_template(
            title="Welcome to Engineering Report Deck!",
            username=username,
            main_content="""
            <p>Congratulations! Your email has been verified and your account is now fully activated.</p>

            <p>You can now access all features of <strong>Engineering Report Deck</strong>, including:</p>

            <ul>
                <li>📝 Create professional engineering reports</li>
                <li>🤖 Get AI-powered suggestions and improvements</li>
                <li>📊 Track your report progress and history</li>
                <li>👥 Collaborate with team members</li>
            </ul>

            <p>We're excited to have you on board and can't wait to see the amazing reports you'll create!</p>
            """,
            button_text="Go to Dashboard",
            button_url=dashboard_url
        )

        text_content = f"""
        Welcome to Engineering Report Deck!

        Hello {username},

        Congratulations! Your email has been verified and your account is now fully activated.

        You can now access all features of Engineering Report Deck, including:

        • Create professional engineering reports
        • Get AI-powered suggestions and improvements  
        • Track your report progress and history
        • Collaborate with team members

        Get started: {dashboard_url}

        We're excited to have you on board and can't wait to see the amazing reports you'll create!

        Best regards,
        The Engineering Report Deck Team
        """

        subject = "🎉 Welcome to Engineering Report Deck!"
        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()