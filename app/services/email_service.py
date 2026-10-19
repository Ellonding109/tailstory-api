# # backend/app/services/email_service.py
# import os
# from urllib.parse import urlencode

# try:
#     import resend
# except ImportError:  # pragma: no cover - optional dependency for dev setups
#     resend = None

# RESEND_API_KEY = os.getenv("RESEND_API_KEY")
# FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# if RESEND_API_KEY and resend is not None:
#     resend.api_key = RESEND_API_KEY


# def build_invitation_link(token: str, frontend_url: str | None = None) -> str:
#     base_url = (frontend_url or FRONTEND_URL).rstrip('/')
#     return f"{base_url}/accept-invite?{urlencode({'token': token})}"


# def send_invitation_email(invited_email: str, pet_name: str, invite_token: str, inviter_email: str):
#     """Send real invitation email via Resend when configured."""
#     accept_url = build_invitation_link(invite_token)

#     email_content = f"""
#     <html>
#     <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
#         <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
#             <h2 style="color: #4F46E5;">You're invited to join {pet_name}'s story! 🐾</h2>
#             <p><strong>{inviter_email}</strong> has invited you to contribute memories to <strong>{pet_name}</strong>'s storybook on TailStory.</p>
#             <p>Together, you can:</p>
#             <ul>
#                 <li>📸 Upload photos and videos</li>
#                 <li>✨ Create AI-powered stories</li>
#                 <li> Preserve precious memories forever</li>
#             </ul>
#             <div style="text-align: center; margin: 30px 0;">
#                 <a href="{accept_url}"
#                    style="background: linear-gradient(135deg, #FF6B6B 0%, #FFB8A3 100%);
#                           color: white;
#                           padding: 15px 40px;
#                           text-decoration: none;
#                           border-radius: 50px;
#                           display: inline-block;
#                           font-weight: bold;
#                           font-size: 16px;">
#                     Accept Invitation
#                 </a>
#             </div>
#             <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
#             <p style="word-break: break-all; color: #4F46E5;">{accept_url}</p>
#             <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
#             <p style="color: #999; font-size: 12px; text-align: center;">
#                 TailStory - Your pet's life, beautifully remembered.
#             </p>
#         </div>
#     </body>
#     </html>
#     """

#     if not RESEND_API_KEY or resend is None:
#         print(f"⚠️ Resend not configured. Invitation link for {invited_email}: {accept_url}")
#         return {"status": "mocked", "accept_url": accept_url}

#     try:
#         email = resend.Emails.send({
#             "from": "TailStory <onboarding@resend.dev>",
#             "to": invited_email,
#             "subject": f"You're invited to {pet_name}'s story on TailStory! 🐾",
#             "html": email_content,
#         })
#         print(f"✅ Invitation email sent to {invited_email}")
#         return email
#     except Exception as e:
#         print(f"❌ Failed to send email: {e}")
#         raise e

# backend/app/services/email_service.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM", "TAILSTORY <noreply@tailstory.com>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

def send_invitation_email(invited_email: str, pet_name: str, invite_token: str, inviter_email: str, custom_message: str = ""):
    """
    Sends an invitation email via SMTP. 
    Abstracted so we can easily swap Gmail for Resend/SendGrid later.
    """
    accept_url = f"{FRONTEND_URL}/accept-invite?token={invite_token}"
    
    # Fallback message if none provided
    message_text = custom_message or f"Come help me add {pet_name}'s memories!"

    html_content = f"""
    <html>
    <body style="font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #2D3436; background-color: #FDF8F3; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
            <h2 style="color: #FF6B6B; font-family: 'Playfair Display', serif; font-size: 28px; margin-top: 0;">You're invited to join {pet_name}'s story! 🐾</h2>
            
            <p style="font-size: 16px;"><strong>{inviter_email}</strong> has invited you to contribute memories to <strong>{pet_name}</strong>'s storybook on TailStory.</p>
            
            <div style="background: #FFF8F0; border-left: 4px solid #FF6B6B; padding: 15px; margin: 20px 0; border-radius: 4px; font-style: italic; color: #636E72;">
                "{message_text}"
            </div>
            
            <p>Together, you can upload photos, create AI-powered stories, and preserve precious memories forever.</p>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{accept_url}" 
                   style="background: linear-gradient(135deg, #FF6B6B 0%, #FFB8A3 100%); 
                          color: white; 
                          padding: 16px 40px; 
                          text-decoration: none; 
                          border-radius: 50px; 
                          display: inline-block; 
                          font-weight: bold;
                          font-size: 16px;
                          box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);">
                    Accept Invitation
                </a>
            </div>
            
            <p style="color: #636E72; font-size: 14px; margin-top: 30px;">Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #4F46E5; font-size: 14px; background: #F5F0E6; padding: 10px; border-radius: 8px;">{accept_url}</p>
            
            <hr style="border: none; border-top: 1px solid #F5F0E6; margin: 40px 0;">
            <p style="color: #9CA3AF; font-size: 12px; text-align: center;">
                TailStory - Your pet's life, beautifully remembered.<br>
                This invitation expires in 7 days.
            </p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"You're invited to {pet_name}'s story on TailStory! 🐾"
    msg["From"] = MAIL_FROM
    msg["To"] = invited_email
    
    msg.attach(MIMEText(html_content, "html"))

    try:
        # Connect to Gmail SMTP server
        print(f"📤 Attempting to send email to {invited_email} via {SMTP_HOST}...")
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Invitation email successfully sent to {invited_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email via SMTP: {e}")
        raise Exception(f"SMTP Error: {str(e)}")

def send_email(to_email: str, subject: str, html_content: str):
    """Sends a beautifully branded email via Resend."""
    if not RESEND_API_KEY:
        print("⚠️ Resend API Key missing. Email not sent.")
        return

    # Premium Branded Template
    branded_html = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #2D3436; background-color: #FFF8F0; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.05);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #FF6B6B 0%, #FFB8A3 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px; font-family: 'Playfair Display', serif;">TailStory 🐾</h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 40px 30px;">
                {html_content}
            </div>
            
            <!-- Footer -->
            <div style="background: #F5F0E6; padding: 20px; text-align: center; font-size: 12px; color: #636E72;">
                <p style="margin: 0;">Your pet's life, beautifully remembered.</p>
                <p style="margin: 5px 0 0 0;">© 2026 TailStory. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from": "TailStory <onboarding@resend.dev>",
            "to": to_email,
            "subject": subject,
            "html": branded_html
        })
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")