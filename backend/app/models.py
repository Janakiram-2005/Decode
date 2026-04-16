from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    admin_secret: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    role: str = "user"
    created_at: datetime

    class Config:
        from_attributes = True

# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Media Models
class MediaResponse(BaseModel):
    media_id: str
    media_type: str
    sha256_hash: str
    file_size: int
    url: Optional[str] = None
    uploaded_at: datetime
    status: str = "success"
    uploader_email: Optional[str] = None  # Added for Admin View
    watermark_present: Optional[bool] = False  # Phase 3: watermark metadata

    class Config:
        from_attributes = True

# Verification Models
class VerificationLog(BaseModel):
    verification_id: str
    admin_user_id: str
    uploaded_hash: str
    match_found: bool
    matched_media_id: Optional[str] = None
    verified_at: datetime
    similarity_score: Optional[float] = None          # Phase 4
    similarity_matched_media_id: Optional[str] = None # Phase 4
    verification_method: Optional[str] = "none"       # Phase 4
    # Phase 5
    tamper_probability: Optional[float] = None
    final_verdict: Optional[str] = None
    confidence_score: Optional[float] = None
    risk_level: Optional[str] = None

class VerificationResponse(BaseModel):
    status: str
    matched: bool
    original_media_id: Optional[str] = None
    original_user_id: Optional[str] = None
    original_upload_date: Optional[datetime] = None
    hashed: str
    verified_at: datetime
    uploader_email: Optional[str] = None
    similarity_info: Optional[dict] = None
    verification_method: Optional[str] = "none"  # watermark, hash, similarity, both, none
    confidence: Optional[str] = "low"
    watermark_version: Optional[str] = None
    watermark_matched: Optional[bool] = False   # Layer 1 result
    hash_matched: Optional[bool] = False        # Layer 2 result
    # Phase 4 ─ Layer 3
    similarity_matched: Optional[bool] = False
    similarity_score: Optional[float] = None
    similarity_matched_media_id: Optional[str] = None
    # Phase 5 ─ Layer 4 + Risk Engine
    tamper_detected: Optional[bool] = False
    tamper_probability: Optional[float] = 0.0
    tamper_method: Optional[str] = None
    final_verdict: Optional[str] = None
    confidence_score: Optional[float] = None
    risk_level: Optional[str] = None
