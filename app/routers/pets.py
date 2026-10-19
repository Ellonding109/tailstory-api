from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Pet, User, PetAccess
from app.schemas import PetCreate, PetResponse
from app.core.security import get_current_user
from app.services.plan_features import check_can_create_pet

router = APIRouter(prefix="/pets", tags=["Pets"])

@router.post("/", response_model=PetResponse)
def create_pet(pet: PetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_can_create_pet(db, current_user.id)
    new_pet = Pet(**pet.dict(), owner_id=current_user.id)
    db.add(new_pet)
    db.commit()
    db.refresh(new_pet)
    return new_pet

@router.get("/", response_model=List[PetResponse])
def get_my_pets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    owned_pets = db.query(Pet).filter(Pet.owner_id == current_user.id).all()
    shared_access = db.query(PetAccess).filter(PetAccess.user_id == current_user.id).all()
    shared_pet_ids = [access.pet_id for access in shared_access]
    
    shared_pets = []
    if shared_pet_ids:
        shared_pets = db.query(Pet).filter(Pet.id.in_(shared_pet_ids)).all()
        
    all_pets_dict = {pet.id: pet for pet in owned_pets + shared_pets}
    return list(all_pets_dict.values())

@router.put("/{pet_id}", response_model=PetResponse)
def update_pet(pet_id: str, pet_update: PetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == current_user.id).first()
    if not db_pet: raise HTTPException(status_code=404, detail="Pet not found")
    for key, value in pet_update.dict(exclude_unset=True).items():
        setattr(db_pet, key, value)
    db.commit()
    db.refresh(db_pet)
    return db_pet

@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet(pet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == current_user.id).first()
    if not db_pet: raise HTTPException(status_code=404, detail="Pet not found")
    db.delete(db_pet)
    db.commit()

# @router.get("/{pet_id}", response_model=PetResponse)
# def get_pet(
#     pet_id: str, 
#     db: Session = Depends(get_db), 
#     current_user: User = Depends(get_current_user)
# ):
#     pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == current_user.id).first()
#     if not pet:
#         access = db.query(PetAccess).filter(
#             PetAccess.pet_id == pet_id,
#             PetAccess.user_id == current_user.id
#         ).first()
#         if not access:
#             raise HTTPException(status_code=404, detail="Pet not found")
#         pet = db.query(Pet).filter(Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
#     return pet