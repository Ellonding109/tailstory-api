from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import User, Pet, Memory, Subscription

PLAN_LIMITS = {
    "free": {"max_pets": 1, "max_memories": 50, "export_pdf": False, "family_sharing": False},
    "premium": {"max_pets": -1, "max_memories": -1, "export_pdf": True, "family_sharing": False},
    "family": {"max_pets": -1, "max_memories": -1, "export_pdf": True, "family_sharing": True}
}

def get_user_plan(db: Session, user_id: str) -> dict:
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.status == "active").first()
    return PLAN_LIMITS.get(subscription.plan if subscription else "free", PLAN_LIMITS["free"])

def check_can_create_pet(db: Session, user_id: str):
    plan = get_user_plan(db, user_id)
    if plan["max_pets"] != -1 and db.query(Pet).filter(Pet.owner_id == user_id).count() >= plan["max_pets"]:
        raise HTTPException(status_code=403, detail="Pet limit reached. Upgrade plan!")

def check_can_create_memory(db: Session, user_id: str):
    plan = get_user_plan(db, user_id)
    if plan["max_memories"] != -1 and db.query(Memory).join(Pet).filter(Pet.owner_id == user_id).count() >= plan["max_memories"]:
        raise HTTPException(status_code=403, detail="Memory limit reached. Upgrade plan!")

def check_can_export_pdf(db: Session, user_id: str):
    # if not get_user_plan(db, user_id)["export_pdf"]:
    #     raise HTTPException(status_code=403, detail="PDF export requires Premium plan.")
    pass