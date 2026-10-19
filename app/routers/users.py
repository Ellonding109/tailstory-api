from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.core.security import get_current_user, get_password_hash, verify_password

router = APIRouter(prefix="/users", tags=["Users"])


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None


@router.get("/me")
def get_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "notification_preferences": current_user.notification_preferences or {},
        "created_at": current_user.created_at,
    }


@router.put("/me")
def update_user_profile(
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.email and request.email != current_user.email:
        if db.query(User).filter(User.email == request.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = request.email

    if request.new_password:
        if not request.current_password:
            raise HTTPException(status_code=400, detail="Current password is required to change password")

        if not verify_password(request.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        current_user.password_hash = get_password_hash(request.new_password)

    if request.notification_preferences is not None:
        current_user.notification_preferences = request.notification_preferences

    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully", "email": current_user.email}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GDPR Compliant Account Deletion: cascades to pets, memories, etc."""
    db.delete(current_user)
    db.commit()
    return None
