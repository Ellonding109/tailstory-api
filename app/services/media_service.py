# backend/app/services/media_service.py
import os
import uuid
from PIL import Image
from fastapi import UploadFile

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_and_compress_image(file: UploadFile) -> str:
    """
    Takes an uploaded image, compresses it, saves it as WebP, 
    and returns the relative URL path.
    """
    # Generate a unique filename to prevent collisions
    unique_filename = f"{uuid.uuid4()}.webp"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Open the image using Pillow
        image = Image.open(file.file)
        
        # Convert to RGB if the image has an alpha channel (RGBA) or palette (P)
        # This is required for saving as JPEG/WebP
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Compress and save as WebP (excellent quality-to-size ratio)
        image.save(file_path, format="WEBP", quality=80, optimize=True)
        
        # Return the URL path that the frontend can use to fetch it
        return f"/uploads/{unique_filename}"
    
    except Exception as e:
        print(f"Error processing image: {e}")
        raise ValueError("Invalid image file")