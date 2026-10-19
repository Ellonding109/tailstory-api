from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
from app.database import get_db
from app.models import User, Subscription
from app.core.security import get_current_user
from app.schemas import SubscriptionPlan, SubscriptionResponse
from app.services.intasend_service import create_checkout_link
from app.services.notification_service import create_notification, notify_admin
import os

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("/my-plan", response_model=SubscriptionResponse)
def get_my_subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not subscription:
        subscription = Subscription(user_id=current_user.id, plan="free", status="active")
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    return subscription

@router.post("/create-checkout-session")
async def create_checkout_session(plan: SubscriptionPlan, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        checkout_data = await create_checkout_link(user_id=current_user.id, user_email=current_user.email, plan=plan.plan)
        
        if os.getenv("INTASEND_MOCK_MODE", "false").lower() == "true":
            subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
            if subscription:
                subscription.plan = plan.plan
                subscription.status = "active"  # Ensure status is active
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            else:
                subscription = Subscription(
                    user_id=current_user.id, 
                    plan=plan.plan, 
                    status="active",  # Ensure status is active
                    current_period_end = datetime.utcnow() + timedelta(days=30)
                )
                db.add(subscription)
            db.commit()
            # Inside create_checkout_session, after updating DB in mock mode:
            create_notification(db, current_user.id, "Plan Upgraded! ", f"You are now on the {plan.plan.capitalize()} plan. Enjoy unlimited memories!", "success", send_email_alert=True)
            notify_admin(db, os.getenv("ADMIN_EMAIL"), "New Subscription Revenue ", f"User {current_user.email} upgraded to {plan.plan.capitalize()}.")
            
        return {"checkout_url": checkout_data["checkout_url"], "session_id": checkout_data["api_ref"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/webhooks/intasend")
async def intasend_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        if payload.get("state") in ["COMPLETED", "SUCCESS"]:
            api_ref = payload.get("api_ref")
            if api_ref and api_ref.startswith("tailstory_sub_"):
                parts = api_ref.split("_")
                user_id, plan = parts[2], parts[3]
                subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
                if subscription:
                    subscription.plan = plan
                    subscription.status = "active"
                    db.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Webhook failed")

@router.get("/plans")
def get_available_plans():
    return {
        "free": {"name": "Free", "price": 0, "features": ["1 pet profile", "50 memories", "Basic AI stories"]},
        "premium": {"name": "Premium", "price": 9.99, "features": ["Unlimited pets", "Unlimited memories", "Advanced AI stories", "HD photo storage", "Export to PDF"]},
        "family": {"name": "Family", "price": 19.99, "features": ["Everything in Premium", "Up to 5 family members", "Shared pet profiles", "Custom keepsakes"]}
    }