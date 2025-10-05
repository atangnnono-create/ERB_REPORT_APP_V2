import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.ethereal.email")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SMTP_USERNAME")
        self.sender_password = os.getenv("SMTP_PASSWORD")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.app_name = "Engineering Report Deck"

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email using SMTP with proper error handling"""
        if not all([self.sender_email, self.sender_password]):
            logger.warning("Email credentials not configured. Skipping email send.")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.app_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Create plain text version
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)

            # HTML version
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(self, to_email: str, verification_token: str, username: str):
        """Send professional email verification"""
        verification_url = f"{self.base_url}/auth/verify-email?token={verification_token}"
        expiration_hours = 24

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Verify Your Email</h1>
                    <p>Engineering Report Deck</p>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Thank you for registering with the Engineering Report Deck. To complete your registration and access all features, please verify your email address by clicking the button below:</p>

                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>

                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 5px;">
                        {verification_url}
                    </p>

                    <p><strong>This verification link will expire in {expiration_hours} hours.</strong></p>

                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Engineering Report Deck. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Verify Your Email Address - Engineering Report Deck

        Hello {username}!

        Thank you for registering with the Engineering Report Deck. To complete your registration, please verify your email address by visiting:

        {verification_url}

        This verification link will expire in {expiration_hours} hours.

        If you didn't create an account with us, please ignore this email.

        Best regards,
        Engineering Report Deck Team
        """

        subject = "🔐 Verify Your Email - Engineering Report Deck"
        return self.send_email(to_email, subject, html_content, text_content)

    def send_welcome_email(self, to_email: str, username: str):
        """Send welcome email after successful verification"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .feature {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome Aboard!</h1>
                    <p>Your email has been verified</p>
                </div>
                <div class="content">
                    <h2>Welcome, {username}!</h2>
                    <p>Your email address has been successfully verified and your account is now fully activated.</p>

                    <h3>What you can do now:</h3>
                    <div class="feature">
                        <strong>📝 Create Professional Reports</strong>
                        <p>Document your engineering competencies with structured templates</p>
                    </div>
                    <div class="feature">
                        <strong>🤖 Get AI Feedback</strong>
                        <p>Receive intelligent suggestions to improve your reports</p>
                    </div>
                    <div class="feature">
                        <strong>📊 Track Your Progress</strong>
                        <p>Monitor your completion status across all competency areas</p>
                    </div>

                    <p>You can now login and start creating your engineering reports:</p>
                    <p><a href="{self.base_url}">{self.base_url}</a></p>

                    <p>If you have any questions, please don't hesitate to contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Engineering Report Deck!

        Hello {username},

        Your email address has been successfully verified and your account is now fully activated.

        You can now access all features including:
        - Create professional engineering reports
        - Receive AI-powered feedback
        - Track your progress across competencies
        - Export your reports

        Login here: {self.base_url}

        Best regards,
        Engineering Report Deck Team
        """

        subject = "🎉 Welcome to Engineering Report Deck!"
        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()