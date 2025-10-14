#!/usr/bin/env python3
"""
Google SMTP Test Script
Tests your SMTP credentials before integrating with the main application
"""

import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime


def test_smtp_connection():
    """Test SMTP connection with your Google credentials"""

    # Your environment variables - update these if different
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", smtp_username)

    # Test recipient - use your own email for testing
    test_to_email = input("Enter your test email address: ").strip()

    print("🔧 Testing SMTP Configuration...")
    print(f"SMTP Server: {smtp_server}:{smtp_port}")
    print(f"SMTP Username: {smtp_username}")
    print(f"From Email: {from_email}")
    print(f"Test Recipient: {test_to_email}")
    print("-" * 50)

    if not all([smtp_username, smtp_password]):
        print("❌ ERROR: SMTP_USERNAME or SMTP_PASSWORD environment variables not set!")
        print("Please check your .env file")
        return False

    try:
        # Step 1: Test SMTP Connection
        print("1. Testing SMTP connection...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.ehlo()
        print("   ✅ SMTP connection established")

        # Step 2: Test STARTTLS
        print("2. Testing STARTTLS encryption...")
        server.starttls()
        server.ehlo()
        print("   ✅ STARTTLS encryption enabled")

        # Step 3: Test Authentication
        print("3. Testing authentication...")
        server.login(smtp_username, smtp_password)
        print("   ✅ Authentication successful")

        # Step 4: Test Email Sending
        print("4. Testing email sending...")

        # Create test email
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("Engineering Report Deck Test", from_email))
        msg['To'] = test_to_email
        msg['Subject'] = "✅ SMTP Test - Engineering Report Deck"
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        # Email content
        html_content = f"""
        <html>
        <body>
            <h2 style="color: #2c3e50;">✅ SMTP Test Successful!</h2>
            <p>This test email confirms that your Google SMTP configuration is working correctly.</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Test Details:</strong><br>
                • Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
                • SMTP Server: {smtp_server}<br>
                • From: {from_email}<br>
                • To: {test_to_email}
            </div>
            <p>If you received this email, your Engineering Report Deck email service is ready to go! 🎉</p>
        </body>
        </html>
        """

        text_content = f"""
        SMTP Test Successful!

        This test email confirms that your Google SMTP configuration is working correctly.

        Test Details:
        • Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        • SMTP Server: {smtp_server}
        • From: {from_email}
        • To: {test_to_email}

        If you received this email, your Engineering Report Deck email service is ready to go!
        """

        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        # Send email
        server.send_message(msg)
        server.quit()

        print("   ✅ Test email sent successfully!")
        print("📧 Email should arrive within 1-2 minutes.")
        print("💡 Check your spam folder if you don't see it in inbox.")

        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print("\n🔧 Troubleshooting:")
        print("• Check if 2FA is enabled on your Google account")
        print("• Verify you're using an App Password (16 characters)")
        print("• Make sure 'Less secure app access' is enabled if not using app password")
        return False

    except smtplib.SMTPConnectError as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print("\n🔧 Troubleshooting:")
        print("• Check SMTP_SERVER and SMTP_PORT in your .env file")
        print("• Verify internet connection")
        print("• Try SMTP port 465 with SSL instead of 587 with STARTTLS")
        return False

    except smtplib.SMTPServerDisconnected as e:
        print(f"❌ SERVER DISCONNECTED: {e}")
        print("\n🔧 Troubleshooting:")
        print("• Google may be blocking the connection")
        print("• Check if your IP address is blocked by Google")
        print("• Try again in a few minutes")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def check_environment():
    """Check if environment variables are loaded"""
    print("🔍 Checking environment variables...")

    required_vars = ['SMTP_USERNAME', 'SMTP_PASSWORD']
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * len(value)} (set)")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False

    return True


if __name__ == "__main__":
    print("🚀 Engineering Report Deck - SMTP Test")
    print("=" * 50)

    # Load environment from .env file if exists
    try:
        from dotenv import load_dotenv

        load_dotenv()
        print("📁 .env file loaded")
    except ImportError:
        print("💡 python-dotenv not installed, using system environment variables")

    if check_environment():
        print("\n" + "=" * 50)
        success = test_smtp_connection()

        if success:
            print("\n🎉 SUCCESS! Your SMTP configuration is working correctly.")
            print("You can now proceed with integrating the email service.")
        else:
            print("\n💥 FAILED! Please fix the issues above before proceeding.")
            sys.exit(1)