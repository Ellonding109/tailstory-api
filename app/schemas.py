from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class PetCreate(BaseModel):
    name: str
    species: str
    breed: Optional[str] = None
    birthday: Optional[str] = None
    gotcha_day: Optional[str] = None
    personality_prompt: Optional[str] = None

class PetResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    species: str
    breed: Optional[str]
    birthday: Optional[datetime]
    gotcha_day: Optional[datetime]
    personality_prompt: Optional[str]
    class Config: from_attributes = True

class MemoryResponse(BaseModel):
    id: str
    pet_id: str
    user_id: str
    memory_type: str
    raw_media_url: Optional[str]
    compressed_media_url: Optional[str]
    raw_audio_text: Optional[str]
    ai_generated_story: Optional[str]
    ai_tags: Optional[Dict[str, Any]]
    memory_date: datetime
    class Config: from_attributes = True

class SubscriptionPlan(BaseModel):
    plan: str

class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    current_period_end: Optional[datetime]
    class Config: from_attributes = True

class InvitationCreate(BaseModel):
    pet_id: str
    email: EmailStr

class InvitationResponse(BaseModel):
    invitation_id: str
    token: str
    expires_at: datetime
    message: str


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
    class Config: from_attributes = True