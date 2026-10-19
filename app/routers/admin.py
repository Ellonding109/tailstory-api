from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Pet, Memory, Subscription
from app.core.security import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

def verify_admin(current_user: User):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verify_admin(current_user)
    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "total_pets": db.query(func.count(Pet.id)).scalar(),
        "total_memories": db.query(func.count(Memory.id)).scalar(),
        "active_subscriptions": db.query(func.count(Subscription.id)).filter(Subscription.status == "active", Subscription.plan != "free").scalar()
    }

@router.get("/users")
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verify_admin(current_user)
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "is_admin": u.is_admin, "created_at": u.created_at, "pet_count": len(u.pets)} for u in users]