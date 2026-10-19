from dotenv import load_dotenv

from app.routers import notification
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import auth, pets, memories, subscriptions, colaborations, admin, notification

# Import models so SQLAlchemy knows to create the tables
from app.models import User, Pet, Memory, Subscription, Invitation, PetAccess

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TailStory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "capacitor://localhost", "ionic://localhost", "https://tailstory.waridike-diasporapropertyconnect.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(pets.router)
app.include_router(memories.router)
app.include_router(subscriptions.router)
app.include_router(colaborations.router)
app.include_router(admin.router)
app.include_router(notification.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to TailStory API 🐾"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}