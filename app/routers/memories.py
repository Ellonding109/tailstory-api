from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from fastapi.responses import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import io

from app.database import get_db
from app.models import Memory, Pet, User, PetAccess
from app.schemas import MemoryResponse
from app.core.security import get_current_user
from app.services import media_service, ai_service
from app.services.plan_features import check_can_create_memory, get_user_plan

router = APIRouter(prefix="/memories", tags=["Memories"])

@router.post("/", response_model=MemoryResponse)
async def create_memory(
    pet_id: str = Form(...),
    memory_date: str = Form(...),
    memory_type: str = Form(...),
    user_note: str = Form(""),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_can_create_memory(db, current_user.id)
    
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == current_user.id).first()
    if not pet:
        access = db.query(PetAccess).filter(PetAccess.pet_id == pet_id, PetAccess.user_id == current_user.id).first()
        if not access:
            raise HTTPException(status_code=404, detail="Pet not found or unauthorized")
        pet = db.query(Pet).filter(Pet.id == pet_id).first()

    compressed_media_url = None
    if file and memory_type == "photo":
        compressed_media_url = media_service.save_and_compress_image(file)

    ai_story = user_note or f"A wonderful memory with {pet.name}."
    ai_tags = {"objects": [], "mood": "unknown", "setting": "unknown"}
    
    if memory_type == "photo" and compressed_media_url:
        try:
            description = ai_service.get_image_description(compressed_media_url)
            ai_result = ai_service.generate_memory_story(pet.name, description, user_note)
            ai_story = ai_result.get("story", user_note)
            ai_tags = ai_result.get("tags", ai_tags)
        except Exception as e:
            print(f"AI Pipeline failed: {e}")

    new_memory = Memory(
        pet_id=pet_id,
        user_id=current_user.id,
        memory_type=memory_type,
        compressed_media_url=compressed_media_url,
        raw_audio_text=user_note if memory_type == "voice" else None,
        ai_generated_story=ai_story,
        ai_tags=ai_tags,
        memory_date=datetime.fromisoformat(memory_date)
    )
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)
    return new_memory

@router.get("/pet/{pet_id}", response_model=List[MemoryResponse])
def get_pet_memories(pet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Memory).filter(Memory.pet_id == pet_id).order_by(Memory.memory_date.desc()).all()

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memory = db.query(Memory).join(Pet).filter(Memory.id == memory_id, Pet.owner_id == current_user.id).first()
    if not memory:
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == current_user.id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found or not authorized")
    db.delete(memory)
    db.commit()

# @router.get("/pet/{pet_id}/export-pdf")
# async def export_pet_storybook(pet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     # Check if user has access to this pet
#     pet = db.query(Pet).filter(Pet.id == pet_id).first()
#     if not pet:
#         raise HTTPException(status_code=404, detail="Pet not found")
    
#     is_owner = pet.owner_id == current_user.id
#     has_access = db.query(PetAccess).filter(
#         PetAccess.pet_id == pet_id,
#         PetAccess.user_id == current_user.id
#     ).first() if not is_owner else True
    
#     if not is_owner and not has_access:
#         raise HTTPException(status_code=403, detail="You don't have access to this pet")
    
#     # Check plan limits
#     user_plan = get_user_plan(db, current_user.id)
    
#     if not user_plan.get('export_pdf', False):
#         raise HTTPException(status_code=403, detail="PDF export requires a Premium or Family plan.")
    
#     # Get memories
#     memories = db.query(Memory).filter(Memory.pet_id == pet_id).order_by(Memory.memory_date.desc()).all()
    
#     if not memories:
#         raise HTTPException(status_code=404, detail="No memories to export")
    
#     # Generate PDF in memory
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
#     story = []
#     styles = getSampleStyleSheet()
    
#     # Title
#     story.append(Paragraph(f"{pet.name}'s Story", styles['Title']))
#     story.append(Paragraph(f"A beautiful journey through memories", styles['Normal']))
#     story.append(Spacer(1, 0.5*inch))
#     story.append(Paragraph(f"Total Memories: {len(memories)}", styles['Normal']))
#     story.append(Spacer(1, 0.5*inch))
    
#     # Memories
#     for i, memory in enumerate(memories, 1):
#         if memory.ai_generated_story:
#             if memory.memory_date:
#                 date_str = memory.memory_date.strftime("%B %d, %Y")
#                 story.append(Paragraph(f"<b>Memory #{i} - {date_str}</b>", styles['Heading2']))
#             else:
#                 story.append(Paragraph(f"<b>Memory #{i}</b>", styles['Heading2']))
            
#             story.append(Paragraph(memory.ai_generated_story, styles['Normal']))
#             story.append(Spacer(1, 0.3*inch))
    
#     doc.build(story)
#     buffer.seek(0)
    
#     safe_filename = f"{pet.name.replace(' ', '_')}_storybook.pdf"
    
#     return Response(
#         content=buffer.getvalue(),
#         media_type='application/pdf',
#         headers={'Content-Disposition': f'attachment; filename="{safe_filename}"'}
#     )

@router.get("/pet/{pet_id}/export-pdf")
async def export_pet_storybook(pet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if user has access to this pet
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    is_owner = pet.owner_id == current_user.id
    has_access = db.query(PetAccess).filter(
        PetAccess.pet_id == pet_id,
        PetAccess.user_id == current_user.id
    ).first() if not is_owner else True
    
    if not is_owner and not has_access:
        raise HTTPException(status_code=403, detail="You don't have access to this pet")
    
    # Check plan limits
    user_plan = get_user_plan(db, current_user.id)
    if not user_plan.get('export_pdf', False):
        raise HTTPException(status_code=403, detail="PDF export requires a Premium or Family plan.")
    
    # Get memories
    memories = db.query(Memory).filter(Memory.pet_id == pet_id).order_by(Memory.memory_date.asc()).all()
    
    if not memories:
        raise HTTPException(status_code=404, detail="No memories to export")
    
    # Generate PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    
    # Create custom styles
    styles = getSampleStyleSheet()
    
    # Custom Title Style (Coral color)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=36,
        textColor='#FF6B6B',  # Coral
        fontName='Helvetica-Bold',
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Subtitle Style (Soft Gray)
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor='#636E72',  # Stone
        fontName='Helvetica-Oblique',
        spaceAfter=20,
        alignment=1
    )
    
    # Section Header Style (Sage color)
    section_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading2'],
        fontSize=18,
        textColor='#9CAF88',  # Sage
        fontName='Helvetica-Bold',
        spaceAfter=15,
        spaceBefore=20,
        keepWithNext=True
    )
    
    # Body Text Style (Charcoal)
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        textColor='#2D3436',  # Charcoal
        fontName='Helvetica',
        leading=18,  # Line spacing
        spaceAfter=15
    )
    
    # Date Style (Soft Coral)
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#FFB8A3',  # Peach
        fontName='Helvetica-Oblique',
        spaceAfter=10
    )
    
    # Closing Style
    closing_style = ParagraphStyle(
        'CustomClosing',
        parent=styles['Normal'],
        fontSize=14,
        textColor='#636E72',
        fontName='Helvetica-Oblique',
        alignment=1,
        spaceAfter=10
    )
    
    # === COVER PAGE ===
    # Add blank space at top
    story.append(Spacer(1, 2*inch))
    
    # Pet Name (Large, Centered, Coral)
    story.append(Paragraph(f"{pet.name}", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Subtitle
    story.append(Paragraph("A Beautiful Journey Through Memories", subtitle_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Decorative line
    story.append(Paragraph("<para alignment='center'><font color='#FFB8A3'>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</font></para>", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Pet details
    if pet.species:
        story.append(Paragraph(f"<b>Species:</b> {pet.species}", body_style))
    if pet.breed:
        story.append(Paragraph(f"<b>Breed:</b> {pet.breed}", body_style))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>Total Memories:</b> {len(memories)}", body_style))
    
    # Created date
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph(f"Created with ❤️ by TailStory", closing_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", date_style))
    
    # Page break
    story.append(PageBreak())
    
    # === TABLE OF CONTENTS (Optional) ===
    story.append(Paragraph("Table of Contents", section_style))
    story.append(Spacer(1, 0.3*inch))
    
    for i, memory in enumerate(memories, 1):
        if memory.memory_date:
            date_str = memory.memory_date.strftime("%B %d, %Y")
            story.append(Paragraph(f"{i}. Memory from {date_str}", body_style))
    
    story.append(PageBreak())
    
    # === MEMORIES SECTION ===
    story.append(Paragraph("Our Precious Memories", section_style))
    story.append(Paragraph("<para alignment='center'><font color='#636E72'>Every moment tells a Story</font></para>", subtitle_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Add each memory
    for i, memory in enumerate(memories, 1):
        # Memory header with number
        story.append(Paragraph(f"Memory {i}", section_style))
        
        # Date (if available)
        if memory.memory_date:
            date_str = memory.memory_date.strftime("%A, %B %d, %Y")
            story.append(Paragraph(f"📅 {date_str}", date_style))
        
        # The AI Story (main content)
        if memory.ai_generated_story:
            # Clean up any markdown or special characters
            clean_story = memory.ai_generated_story.replace('**', '').replace('##', '').replace('#', '')
            story.append(Paragraph(clean_story, body_style))
        
        # Tags (if available)
        if memory.ai_tags:
            tags_html = ""
            if memory.ai_tags.get('mood') and memory.ai_tags['mood'] != 'unknown':
                tags_html += f"😊 <b>Mood:</b> {memory.ai_tags['mood'].capitalize()} &nbsp;&nbsp; "
            if memory.ai_tags.get('setting') and memory.ai_tags['setting'] != 'unknown':
                tags_html += f"📍 <b>Setting:</b> {memory.ai_tags['setting'].capitalize()} &nbsp;&nbsp; "
            if memory.ai_tags.get('objects') and len(memory.ai_tags['objects']) > 0:
                objects = ', '.join(memory.ai_tags['objects'][:3])  # Show first 3 objects
                tags_html += f"️ <b>Features:</b> {objects}"
            
            if tags_html:
                story.append(Paragraph(f"<font color='#9CAF88'>{tags_html}</font>", body_style))
        
        # Add spacing between memories
        story.append(Spacer(1, 0.5*inch))
        
        # Add decorative separator every 3 memories
        if i % 3 == 0 and i < len(memories):
            story.append(Paragraph("<para alignment='center'><font color='#FFB8A3'>✦ ✦ ✦</font></para>", styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
    
    # Page break before closing
    story.append(PageBreak())
    
    # === CLOSING PAGE ===
    story.append(Spacer(1, 2*inch))
    
    # Heartfelt closing message
    story.append(Paragraph("Thank You for Preserving These Moments", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    closing_message = f"""
    <para alignment='center'>
    Every tail wag, every playful moment, every quiet afternoon—<br/>
    these are the treasures that make {pet.name}'s story so special.<br/><br/>
    
    <font color='#636E72'>
    Cherish these memories forever.<br/>
    They are the proof of an unconditional love<br/>
    that will last a lifetime.
    </font>
    </para>
    """
    story.append(Paragraph(closing_message, body_style))
    
    story.append(Spacer(1, 1*inch))
    
    # Decorative element
    story.append(Paragraph("<para alignment='center'><font color='#FF6B6B' size='24'>🐾</font></para>", styles['Normal']))
    
    story.append(Spacer(1, 1*inch))
    
    # Final branding
    story.append(Paragraph("Created with", closing_style))
    story.append(Paragraph("<font color='#FF6B6B' size='18'><b>TailStory</b></font>", title_style))
    story.append(Paragraph("<font color='#636E72'>Your pet's life, beautifully remembered.</font>", subtitle_style))
    
    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    
    safe_filename = f"{pet.name.replace(' ', '_')}_Storybook.pdf"
    
    return Response(
        content=buffer.getvalue(),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{safe_filename}"'}
    )