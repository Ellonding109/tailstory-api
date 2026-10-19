from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

class Pet(Base):
    __tablename__ = "pets"
    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    breed = Column(String, nullable=True)
    birthday = Column(DateTime(timezone=True), nullable=True)
    gotcha_day = Column(DateTime(timezone=True), nullable=True)
    personality_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="pets")
    memories = relationship("Memory", back_populates="pet", cascade="all, delete-orphan")

class Memory(Base):
    __tablename__ = "memories"
    id = Column(String, primary_key=True, default=generate_uuid)
    pet_id = Column(String, ForeignKey("pets.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    memory_type = Column(String, nullable=False)
    raw_media_url = Column(String, nullable=True)
    compressed_media_url = Column(String, nullable=True)
    raw_audio_text = Column(Text, nullable=True)
    ai_generated_story = Column(Text, nullable=True)
    ai_tags = Column(JSON, nullable=True)
    memory_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pet = relationship("Pet", back_populates="memories")
    user = relationship("User", back_populates="memories")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan = Column(String, default="free")
    status = Column(String, default="active")
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")

class Invitation(Base):
    __tablename__ = "invitations"
    id = Column(String, primary_key=True, default=generate_uuid)
    pet_id = Column(String, ForeignKey("pets.id"), nullable=False)
    invited_email = Column(String, nullable=False)
    invited_by = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PetAccess(Base):
    __tablename__ = "pet_access"
    id = Column(String, primary_key=True, default=generate_uuid)
    pet_id = Column(String, ForeignKey("pets.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    permission = Column(String, default="contributor")
    granted_at = Column(DateTime(timezone=True), server_default=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info") # info, success, warning
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())