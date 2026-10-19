# backend/app/services/notification_service.py
from sqlalchemy.orm import Session
from app.models import Notification, User
from app.services.email_service import send_email

def create_notification(db: Session, user_id: str, title: str, message: str, notif_type: str = "info", send_email_alert: bool = False):
    """Creates an in-app notification and optionally sends an email."""
    
    # 1. Save to Database (In-App)
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type
    )
    db.add(notification)
    db.commit()
    
    # 2. Send Email (if requested)
    if send_email_alert:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            send_email(
                to_email=user.email,
                subject=f"TailStory: {title}",
                html_content=f"<h2>{title}</h2><p>{message}</p><p>Log in to your dashboard to view more details.</p>"
            )

def notify_admin(db: Session, admin_email: str, title: str, message: str):
    """Sends an email directly to the admin."""
    send_email(
        to_email=admin_email,
        subject=f"Admin Alert: {title}",
        html_content=f"<h2>{title}</h2><p>{message}</p>"
    )