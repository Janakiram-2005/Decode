from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from app.database import get_database
from app.models import MediaResponse
from app.routes.auth import get_current_user
from app.utils.hashing import generate_sha256
from app.utils.cloudinary_utils import upload_to_cloudinary
from app.utils.image_similarity import calculate_image_phash
from app.utils.text_similarity import extract_raw_text
from app.utils.encryption import encrypt_user_id
from app.utils.image_watermark import embed_image_watermark
from app.utils.text_watermark import embed_text_watermark
import io
import shutil
import os
import uuid
from datetime import datetime
from typing import List

router = APIRouter()

UPLOAD_DIR_IMAGES = "uploads/images"
UPLOAD_DIR_TEXTS = "uploads/texts"

# Ensure directories exist
os.makedirs(UPLOAD_DIR_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_DIR_TEXTS, exist_ok=True)

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
ALLOWED_TEXT_TYPES = ["text/plain"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload", response_model=MediaResponse)
async def upload_media(
    file: UploadFile = File(...),
    media_type: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    if media_type not in ["image", "text"]:
        raise HTTPException(status_code=400, detail="Invalid media type. Must be 'image' or 'text'")
    
    # Validate content type
    if media_type == "image" and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image file type. Allowed: jpg, jpeg, png")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    if media_type == "image":
        save_path = os.path.join(UPLOAD_DIR_IMAGES, unique_filename)
    else:
        save_path = os.path.join(UPLOAD_DIR_TEXTS, unique_filename)
    
    try:
        # Save file with size limit enforcement during stream
        file_size_counter = 0
        with open(save_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 64) # 64KB chunks
                if not chunk:
                    break
                file_size_counter += len(chunk)
                if file_size_counter > MAX_FILE_SIZE:
                    buffer.close()
                    os.remove(save_path)
                    raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
                buffer.write(chunk)
            
        # Hash the raw file BEFORE watermarking — used to match the original during verification
        original_sha256 = generate_sha256(save_path)
        
        # --- PHASE 3: WATERMARK EMBEDDING ---
        # 1. Encrypt User Identity
        encrypted_token = encrypt_user_id(current_user["user_id"])
        
        # 2. Embed Watermark
        watermark_embedded = False
        try:
            if media_type == "image":
                new_path = embed_image_watermark(save_path, encrypted_token)
                save_path = new_path  # MUST update: .jpg renamed to .png
                watermark_embedded = True
                print(f"[upload] Watermark embedded -> {save_path}")
            elif media_type == "text":
                embed_text_watermark(save_path, encrypted_token)
                watermark_embedded = True
                print(f"[upload] Text watermark embedded -> {save_path}")
        except Exception as e:
            import traceback as _tb
            print(f"[upload] WARNING: Watermarking FAILED: {e}")
            _tb.print_exc()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file locally: {str(e)}")
        
    # File size already validated during stream
    file_size = os.path.getsize(save_path)
    
    # Generate Hash of WATERMARKED file (for exact watermarked-copy matching)
    sha256_hash = generate_sha256(save_path)
    
    db = get_database()
    
    # Duplicate Check
    existing_media = await db.media.find_one({"sha256_hash": sha256_hash})
    if existing_media:
        os.remove(save_path)
        raise HTTPException(status_code=409, detail=f"Duplicate file detected (Hash Match).")

    # Cloudinary Upload (Watermarked version)
    cloudinary_url = None
    if media_type == "image":
        try:
            with open(save_path, "rb") as f:
                upload_result = upload_to_cloudinary(f, folder="media_verification/images")
                cloudinary_url = upload_result.get("url")
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")

    media_id = str(uuid.uuid4())
    
    # pHash (image only) — for Layer 3 image similarity
    phash = None
    if media_type == "image":
        try:
            phash = calculate_image_phash(save_path)
        except Exception as e:
            print(f"[upload] pHash failed: {e}")

    # Extract raw text (text files only) — for Layer 3 text similarity
    extracted_text = None
    if media_type == "text":
        try:
            extracted_text = extract_raw_text(save_path)
        except Exception as e:
            print(f"[upload] Text extraction failed: {e}")

    media_doc = {
        "media_id": media_id,
        "user_id": current_user["user_id"],
        "media_type": media_type,
        "file_path": save_path,
        "url": cloudinary_url,
        "sha256_hash": sha256_hash,           # hash of watermarked file
        "original_sha256": original_sha256,   # hash of original pre-watermark file
        "phash": phash,                        # perceptual hash for Layer 3 image similarity
        "extracted_text": extracted_text,      # raw text for Layer 3 text similarity
        "file_size": file_size,
        "uploaded_at": datetime.utcnow(),
        "watermark_present": watermark_embedded,
        "encrypted_token": encrypted_token
    }
    
    await db.media.insert_one(media_doc)
    
    return media_doc

@router.get("/my-uploads")
async def get_my_uploads(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.media.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}  # exclude MongoDB _id field
    ).sort("uploaded_at", -1)
    docs = await cursor.to_list(length=1000)
    # Normalize each doc so the frontend always gets the expected fields
    result = []
    for doc in docs:
        result.append({
            "media_id":    doc.get("media_id", ""),
            "media_type":  doc.get("media_type", "unknown"),
            "sha256_hash": doc.get("sha256_hash", ""),
            "file_size":   doc.get("file_size", 0),
            "url":         doc.get("url"),
            "uploaded_at": doc.get("uploaded_at"),
            "status":      doc.get("status", "success"),
            "watermark_present": doc.get("watermark_present", False),
        })
    return result

@router.get("/my-uploads/{media_id}/download")
async def download_media(media_id: str, current_user: dict = Depends(get_current_user)):
    """Download the watermarked file for a given media_id (owner only)."""
    from fastapi.responses import FileResponse
    db = get_database()
    media = await db.media.find_one({"media_id": media_id})
    if not media:
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Allow if owner OR if current user is admin
    if media["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    
    file_path = media.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not available on server.")
    
    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=f"watermarked_{filename}",
        media_type="application/octet-stream"
    )

@router.delete("/my-uploads/{media_id}")
async def delete_media(media_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a media file owned by the current user.
    - Removes record from MongoDB
    - Deletes local file from disk
    - Deletes from Cloudinary if applicable
    """
    db = get_database()
    media = await db.media.find_one({"media_id": media_id, "user_id": current_user["user_id"]})
    if not media:
        raise HTTPException(status_code=404, detail="File not found or access denied.")

    # 1. Delete local file
    file_path = media.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Could not delete local file: {e}")

    # 2. Delete from Cloudinary (if stored)
    cloudinary_public_id = media.get("cloudinary_public_id")
    if cloudinary_public_id:
        try:
            import cloudinary.uploader
            cloudinary.uploader.destroy(cloudinary_public_id)
        except Exception as e:
            print(f"Cloudinary delete failed: {e}")

    # 3. Remove from MongoDB
    await db.media.delete_one({"media_id": media_id})

    return {"status": "deleted", "media_id": media_id}

