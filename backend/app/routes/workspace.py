from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks
from app.database import get_database
from app.routes.auth import get_current_user
from app.utils.encryption import encrypt_user_id
from app.utils.image_watermark import embed_image_watermark
from app.utils.text_watermark import embed_text_watermark
import os
import shutil
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List

router = APIRouter()

WORKSPACE_DIR = "uploads/workspace_docs"
TEMP_DIR = "uploads/temp_downloads"

os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
ALLOWED_TEXT_TYPES = ["text/plain"]
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

class WorkspaceDocResponse(BaseModel):
    doc_id: str
    filename: str
    media_type: str
    file_size: int
    uploaded_at: datetime
    uploaded_by: str

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Failed to delete temp file {path}: {e}")

@router.post("/upload", response_model=WorkspaceDocResponse)
async def upload_workspace_doc(
    file: UploadFile = File(...),
    media_type: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload to workspace.")

    if media_type not in ["image", "text"]:
        raise HTTPException(status_code=400, detail="Invalid media type. Must be 'image' or 'text'")

    if media_type == "image" and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image file type. Allowed: jpg, jpeg, png")

    file_extension = os.path.splitext(file.filename)[1].lower()
    doc_id = str(uuid.uuid4())
    unique_filename = f"{doc_id}{file_extension}"
    save_path = os.path.join(WORKSPACE_DIR, unique_filename)

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save workspace file: {str(e)}")

    file_size = os.path.getsize(save_path)
    
    doc = {
        "doc_id": doc_id,
        "filename": file.filename,
        "media_type": media_type,
        "file_path": save_path,
        "file_size": file_size,
        "uploaded_by": current_user["email"],
        "uploaded_at": datetime.utcnow()
    }

    db = get_database()
    await db.workspace_docs.insert_one(doc)

    return doc

@router.get("/list", response_model=List[WorkspaceDocResponse])
async def list_workspace_docs(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.workspace_docs.find({}, {"_id": 0}).sort("uploaded_at", -1)
    docs = await cursor.to_list(length=100)
    return docs

@router.get("/download/{doc_id}")
async def download_workspace_doc(
    doc_id: str, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    doc = await db.workspace_docs.find_one({"doc_id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    original_path = doc.get("file_path")
    if not original_path or not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Original file not available on server.")

    # 1. Create a copy in temp directory
    file_ext = os.path.splitext(original_path)[1]
    temp_filename = f"temp_{uuid.uuid4()}{file_ext}"
    temp_path = os.path.join(TEMP_DIR, temp_filename)
    
    shutil.copy2(original_path, temp_path)

    # 2. Encrypt the downloader's user_id
    encrypted_token = encrypt_user_id(current_user["user_id"])

    # 3. Apply on-the-fly watermark
    try:
        media_type = doc.get("media_type")
        if media_type == "image":
            # embed_image_watermark returns the new path (might be converted to PNG)
            watermarked_path = embed_image_watermark(temp_path, encrypted_token)
            # Remove the original temp copy if embed_image_watermark didn't overwrite it
            if temp_path != watermarked_path and os.path.exists(temp_path):
                os.remove(temp_path)
            temp_path = watermarked_path
            
            # Record dynamic download log
            log_doc = {
                "download_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "user_id": current_user["user_id"],
                "downloaded_at": datetime.utcnow()
            }
            await db.workspace_downloads.insert_one(log_doc)
            
            background_tasks.add_task(remove_file, temp_path)
            
            # Provide an appropriate filename
            download_filename = f"secure_{os.path.splitext(doc['filename'])[0]}.png"
            return FileResponse(temp_path, filename=download_filename, media_type="image/png")

        elif media_type == "text":
            # Modifies the temp file in place
            embed_text_watermark(temp_path, encrypted_token)
            
            log_doc = {
                "download_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "user_id": current_user["user_id"],
                "downloaded_at": datetime.utcnow()
            }
            await db.workspace_downloads.insert_one(log_doc)

            background_tasks.add_task(remove_file, temp_path)
            
            download_filename = f"secure_{doc['filename']}"
            return FileResponse(temp_path, filename=download_filename, media_type="text/plain")

    except Exception as e:
        # Cleanup on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to watermark file: {str(e)}")

@router.delete("/{doc_id}")
async def delete_workspace_doc(doc_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete workspace docs.")

    db = get_database()
    doc = await db.workspace_docs.find_one({"doc_id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    original_path = doc.get("file_path")
    if original_path and os.path.exists(original_path):
        os.remove(original_path)

    await db.workspace_docs.delete_one({"doc_id": doc_id})
    return {"message": "Document deleted successfully."}
