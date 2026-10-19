# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta
# import secrets
# from app.database import get_db
# from app.models import User, Pet, Invitation, PetAccess
# from app.schemas import InvitationCreate, InvitationResponse
# from app.core.security import get_current_user
# from app.services.email_service import send_invitation_email
# from sqlalchemy.orm import joinedload
# from app.services.notification_service import create_notification, notify_admin
# import os

# router = APIRouter(prefix="/collaboration", tags=["Collaboration"])

# @router.post("/invite", response_model=InvitationResponse)
# def invite_to_pet(invitation_data: InvitationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     pet = db.query(Pet).filter(Pet.id == invitation_data.pet_id, Pet.owner_id == current_user.id).first()
#     if not pet: raise HTTPException(status_code=404, detail="Pet not found or not authorized")
    
#     token = secrets.token_urlsafe(32)
#     expires_at = datetime.utcnow() + timedelta(days=7)
    
#     invitation = Invitation(pet_id=invitation_data.pet_id, invited_email=invitation_data.email, invited_by=current_user.id, token=token, expires_at=expires_at)
#     db.add(invitation)
#     db.commit()
#     db.refresh(invitation)
    
#     try:
#         send_invitation_email(invitation_data.email, pet.name, token, current_user.email)
#     except Exception as e:
#         db.delete(invitation)
#         db.commit()
#         raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
        
#     return {"invitation_id": invitation.id, "token": token, "expires_at": expires_at, "message": "Invitation sent"}

# @router.get("/validate/{token}")
# def validate_invitation(token: str, db: Session = Depends(get_db)):
#     invitation = db.query(Invitation).filter(Invitation.token == token, Invitation.status == "pending").first()
#     if not invitation: raise HTTPException(status_code=404, detail="Invalid or expired invitation")
#     if datetime.utcnow() > invitation.expires_at: raise HTTPException(status_code=400, detail="Invitation has expired")
#     pet = db.query(Pet).filter(Pet.id == invitation.pet_id).first()
#     return {"pet_id": invitation.pet_id, "pet_name": pet.name, "inviter_email": invitation.inviter.email, "invited_email": invitation.invited_email}

# @router.post("/accept/{token}")
# def accept_invitation(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     pet = db.query(Pet).filter(Pet.id == invitation.pet_id).first()
#     invitation = db.query(Invitation).filter(Invitation.token == token, Invitation.status == "pending").first()
#     if not invitation: raise HTTPException(status_code=404, detail="Invalid invitation")
#     if invitation.invited_email != current_user.email: raise HTTPException(status_code=403, detail="Email does not match")
#     owner = db.query(User).filter(User.id == pet.owner_id).first()
#     if owner:
#         create_notification(db, owner.id, "Family Member Joined! ‍👩‍👧", f"{current_user.email} has accepted your invite and is now contributing to {pet.name}'s story.", "success", send_email_alert=True)
#     access = PetAccess(pet_id=invitation.pet_id, user_id=current_user.id, permission="contributor")
#     invitation.status = "accepted"
#     db.add(access)
#     db.commit()
#     return {"message": "Access granted"}

# # @router.get("/pet/{pet_id}/collaborators")
# # def get_collaborators(pet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
# #     return db.query(PetAccess).filter(PetAccess.pet_id == pet_id).all()

# @router.get("/pet/{pet_id}/collaborators")
# def get_collaborators(pet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     pet = db.query(Pet).filter(Pet.id == pet_id).first()
#     if not pet:
#         raise HTTPException(status_code=404, detail="Pet not found")
    
#     is_owner = pet.owner_id == current_user.id
#     has_access = db.query(PetAccess).filter(
#         PetAccess.pet_id == pet_id,
#         PetAccess.user_id == current_user.id
#     ).first() if not is_owner else True
    
#     if not is_owner and not has_access:
#         raise HTTPException(status_code=403, detail="You don't have access to view collaborators")
    
#     # Join with User table to get the email
#     collaborators = db.query(PetAccess, User.email).join(
#         User, PetAccess.user_id == User.id
#     ).filter(
#         PetAccess.pet_id == pet_id
#     ).all()
    
#     return [
#         {
#             "user_id": access.user_id,
#             "user_email": email,
#             "permission": access.permission,
#             "granted_at": access.granted_at
#         }
#         for access, email in collaborators
#     ]


# @router.delete("/pet/{pet_id}/collaborators/{user_id}")
# def remove_collaborator(pet_id: str, user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == current_user.id).first()
#     if not pet: raise HTTPException(status_code=404, detail="Not authorized")
#     access = db.query(PetAccess).filter(PetAccess.pet_id == pet_id, PetAccess.user_id == user_id).first()
#     if not access: raise HTTPException(status_code=404, detail="Collaborator not found")
#     db.delete(access)
#     db.commit()
#     return {"message": "Removed"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from app.database import get_db
from app.models import User, Pet, Invitation, PetAccess
from app.schemas import InvitationCreate, InvitationResponse
from app.core.security import get_current_user
from app.services.email_service import send_invitation_email
from app.services.notification_service import create_notification

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])

@router.post("/invite", response_model=InvitationResponse)
def invite_to_pet(invitation_data: InvitationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Verify ownership
    pet = db.query(Pet).filter(Pet.id == invitation_data.pet_id, Pet.owner_id == current_user.id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found or not authorized")
        
    # 2. Build token and dates
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    invitation = Invitation(
        pet_id=invitation_data.pet_id,
        invited_email=invitation_data.email,
        invited_by=current_user.id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    # 3. Attempt email transmission
    try:
        send_invitation_email(invitation_data.email, pet.name, token, current_user.email)
    except Exception as e:
        db.delete(invitation)
        db.commit()
        # This is where your current 500 is thrown. 
        # Check server logs to read the exact value of string {e}
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
        
    return {
        "invitation_id": invitation.id,
        "token": token,
        "expires_at": expires_at,
        "message": "Invitation sent"
    }

@router.get("/validate/{token}")
def validate_invitation(token: str, db: Session = Depends(get_db)):
    invitation = db.query(Invitation).filter(Invitation.token == token, Invitation.status == "pending").first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
        
    if datetime.utcnow() > invitation.expires_at:
        raise HTTPException(status_code=400, detail="Invitation has expired")
        
    pet = db.query(Pet).filter(Pet.id == invitation.pet_id).first()
    return {
        "pet_id": invitation.pet_id,
        "pet_name": pet.name if pet else "Unknown",
        "inviter_email": invitation.inviter.email,
        "invited_email": invitation.invited_email
    }

@router.post("/accept/{token}")
def accept_invitation(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # FIXED: Fetch the invitation first so you can grab the pet_id safely
    invitation = db.query(Invitation).filter(Invitation.token == token, Invitation.status == "pending").first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation")
        
    if invitation.invited_email != current_user.email:
        raise HTTPException(status_code=403, detail="Email does not match")
        
    pet = db.query(Pet).filter(Pet.id == invitation.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Associated pet not found")
        
    owner = db.query(User).filter(User.id == pet.owner_id).first()
    if owner:
        create_notification(
            db, 
            owner.id, 
            "Family Member Joined! 👩‍👧", 
            f"{current_user.email} has accepted your invite and is now contributing to {pet.name}'s story.", 
            "success", 
            send_email_alert=True
        )
        
    access = PetAccess(pet_id=invitation.pet_id, user_id=current_user.id, permission="contributor")
    invitation.status = "accepted"
    
    db.add(access)
    db.commit()
    return {"message": "Access granted"}

@router.get("/pet/{pet_id}/collaborators")
def get_collaborators(pet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
        
    is_owner = pet.owner_id == current_user.id
    has_access = db.query(PetAccess).filter(
        PetAccess.pet_id == pet_id,
        PetAccess.user_id == current_user.id
    ).first()
    
    if not is_owner and not has_access:
        raise HTTPException(status_code=403, detail="You don't have access to view collaborators")
        
    collaborators = db.query(PetAccess, User.email).join(
        User, PetAccess.user_id == User.id
    ).filter(
        PetAccess.pet_id == pet_id
    ).all()
    
    return [
        {
            "user_id": access.user_id,
            "user_email": email,
            "permission": access.permission,
            "granted_at": access.granted_at
        } for access, email in collaborators
    ]

@router.delete("/pet/{pet_id}/collaborators/{user_id}")
def remove_collaborator(pet_id: str, user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == current_user.id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Not authorized")
        
    access = db.query(PetAccess).filter(PetAccess.pet_id == pet_id, PetAccess.user_id == user_id).first()
    if not access:
        raise HTTPException(status_code=404, detail="Collaborator not found")
        
    db.delete(access)
    db.commit()
    return {"message": "Removed"}
