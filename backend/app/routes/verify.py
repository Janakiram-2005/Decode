from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.database import get_database
from app.routes.auth import get_current_user
from app.models import VerificationResponse
import hashlib
import uuid
from datetime import datetime
import os
from app.utils.encryption import decrypt_token
from app.utils.image_watermark import extract_image_watermark
from app.utils.text_watermark import extract_text_watermark
from app.utils.image_similarity import calculate_image_phash, find_best_image_match
from app.utils.text_similarity import extract_raw_text, find_best_text_match
from app.utils.image_tamper_detector import detect_image_tamper
from app.utils.text_tamper_detection import detect_text_tamper
from app.utils.risk_engine import compute_risk_score

router = APIRouter()

TEMP_VERIFY_DIR = "uploads/temp_verify"
os.makedirs(TEMP_VERIFY_DIR, exist_ok=True)


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def _detect_media_type(content_type: str, filename: str) -> str:
    """Detect 'image' or 'text' from content-type with fallback to extension."""
    if content_type:
        if content_type.startswith("image"):
            return "image"
        if content_type.startswith("text"):
            return "text"
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
        return "image"
    if ext in [".txt", ".csv", ".md", ".log"]:
        return "text"
    return "unknown"


@router.post("/verify", response_model=VerificationResponse)
async def verify_media(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")

    # ── Save temp file ─────────────────────────────────────────────────────────
    file_ext = os.path.splitext(file.filename)[1]
    temp_path = os.path.join(TEMP_VERIFY_DIR, f"verify_{uuid.uuid4()}{file_ext}")
    content = await file.read()

    # Guard: max 10 MB
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB.")

    with open(temp_path, "wb") as f:
        f.write(content)

    sha256_hash = hashlib.sha256(content).hexdigest()
    verified_at = datetime.utcnow()
    db = get_database()
    media_type = _detect_media_type(file.content_type, file.filename)

    # ── Base result ────────────────────────────────────────────────────────────
    result_data = {
        "status": "no_match",
        "matched": False,
        "hashed": sha256_hash,
        "verified_at": verified_at,
        "verification_method": "none",
        "confidence": "low",
        "watermark_version": None,
        "watermark_matched": False,
        "hash_matched": False,
        # Phase 5 defaults
        "tamper_detected": False,
        "tamper_probability": 0.0,
        "tamper_method": None,
        "final_verdict": None,
        "confidence_score": None,
        "risk_level": None,
    }

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 1: WATERMARK CHECK
    # ══════════════════════════════════════════════════════════════════════════
    extracted_token = None
    try:
        if media_type == "image":
            extracted_token = extract_image_watermark(temp_path)
        elif media_type == "text":
            extracted_token = extract_text_watermark(temp_path)
    except Exception as e:
        print(f"[verify] Watermark extraction error: {e}")

    watermark_user_id = None
    if extracted_token:
        try:
            decrypted = decrypt_token(extracted_token)
            if decrypted and _is_valid_uuid(decrypted):
                watermark_user_id = decrypted
                result_data["watermark_matched"] = True
                result_data["original_user_id"] = decrypted
                result_data["watermark_version"] = "v1"
                print(f"[verify] Watermark match: user_id={decrypted}")

                uploader = await db.users.find_one({"user_id": decrypted})
                if uploader:
                    result_data["uploader_email"] = uploader["email"]
            else:
                print(f"[verify] Decrypted token not a valid UUID: {decrypted!r}")
        except Exception as e:
            print(f"[verify] Watermark decrypt error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 2: HASH CHECK
    # ══════════════════════════════════════════════════════════════════════════
    hash_match_doc = await db.media.find_one({
        "$or": [
            {"sha256_hash": sha256_hash},
            {"original_sha256": sha256_hash}
        ]
    })

    if hash_match_doc:
        result_data["hash_matched"] = True
        result_data["original_media_id"] = hash_match_doc["media_id"]
        result_data["original_upload_date"] = hash_match_doc.get("uploaded_at")
        print(f"[verify] Hash match: media_id={hash_match_doc['media_id']}")

        if not result_data.get("uploader_email"):
            h_uploader = await db.users.find_one({"user_id": hash_match_doc["user_id"]})
            if h_uploader:
                result_data["uploader_email"] = h_uploader["email"]
        if not result_data.get("original_user_id"):
            result_data["original_user_id"] = hash_match_doc["user_id"]

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 3: SIMILARITY CHECK
    # ══════════════════════════════════════════════════════════════════════════
    similarity_matched = False
    similarity_score = 0.0
    similarity_matched_media_id = None
    matched_original_text = None

    try:
        candidate_cursor = db.media.find(
            {"media_type": media_type},
            {"_id": 0, "media_id": 1, "phash": 1, "extracted_text": 1, "user_id": 1, "uploaded_at": 1}
        ).sort("uploaded_at", -1).limit(100)
        candidates = await candidate_cursor.to_list(length=100)

        if media_type == "image":
            query_phash = calculate_image_phash(temp_path)
            if query_phash:
                best_doc, best_score = find_best_image_match(query_phash, candidates)
                similarity_score = best_score
                if best_doc:
                    similarity_matched = True
                    similarity_matched_media_id = best_doc["media_id"]
                    print(f"[verify] Layer 3 IMAGE similarity: {best_score:.1f}% -> {best_doc['media_id']}")

        elif media_type == "text":
            target_text = extract_raw_text(temp_path)
            if target_text:
                best_doc, best_score = find_best_text_match(target_text, candidates)
                similarity_score = best_score
                if best_doc:
                    similarity_matched = True
                    similarity_matched_media_id = best_doc["media_id"]
                    matched_original_text = best_doc.get("extracted_text", "")
                    print(f"[verify] Layer 3 TEXT similarity: {best_score:.1f}% -> {best_doc['media_id']}")
    except Exception as e:
        print(f"[verify] Layer 3 similarity error: {e}")

    result_data["similarity_matched"] = similarity_matched
    result_data["similarity_score"] = round(similarity_score, 2)
    result_data["similarity_matched_media_id"] = similarity_matched_media_id

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 4: ML TAMPER DETECTION
    # ══════════════════════════════════════════════════════════════════════════
    tamper_probability = 0.0
    tamper_detected = False
    tamper_method = None

    try:
        if media_type == "image":
            tamper_result = detect_image_tamper(temp_path)
            tamper_probability = tamper_result["tamper_probability"]
            tamper_detected = tamper_result["tamper_detected"]
            tamper_method = tamper_result["method"]
            print(f"[verify] Layer 4 IMAGE tamper: prob={tamper_probability:.2f} detected={tamper_detected}")

        elif media_type == "text":
            # Compare against matched document text (if similarity hit) or skip
            if matched_original_text:
                query_text = extract_raw_text(temp_path)
                tamper_result = detect_text_tamper(matched_original_text, query_text)
                tamper_probability = tamper_result["modification_score"]
                tamper_detected = tamper_result["tamper_detected"]
                tamper_method = tamper_result["method"]
                print(f"[verify] Layer 4 TEXT tamper: mod_score={tamper_probability:.2f}")
    except Exception as e:
        print(f"[verify] Layer 4 tamper error: {e}")

    result_data["tamper_detected"] = tamper_detected
    result_data["tamper_probability"] = round(tamper_probability, 4)
    result_data["tamper_method"] = tamper_method

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 5: RISK SCORE AGGREGATION
    # ══════════════════════════════════════════════════════════════════════════
    risk = compute_risk_score(
        watermark_matched=result_data["watermark_matched"],
        hash_matched=result_data["hash_matched"],
        similarity_score=similarity_score,
        tamper_probability=tamper_probability,
    )
    result_data["final_verdict"] = risk["final_verdict"]
    result_data["confidence_score"] = risk["confidence_score"]
    result_data["risk_level"] = risk["risk_level"]

    # ══════════════════════════════════════════════════════════════════════════
    # FINAL STATUS (Phase 4 compat field kept for UI)
    # ══════════════════════════════════════════════════════════════════════════
    wm = result_data["watermark_matched"]
    hm = result_data["hash_matched"]
    sm = result_data["similarity_matched"]

    if wm and hm:
        result_data["matched"] = True
        result_data["status"] = "full_match"
        result_data["verification_method"] = "both"
        result_data["confidence"] = "high"
    elif wm:
        result_data["matched"] = True
        result_data["status"] = "watermark_match"
        result_data["verification_method"] = "watermark"
        result_data["confidence"] = "high"
    elif hm:
        result_data["matched"] = True
        result_data["status"] = "hash_match"
        result_data["verification_method"] = "hash"
        result_data["confidence"] = "medium"
    elif sm:
        result_data["matched"] = True
        result_data["status"] = "similar_media_found"
        result_data["verification_method"] = "similarity"
        result_data["confidence"] = "medium"
    elif tamper_detected:
        result_data["matched"] = True
        result_data["status"] = "tampered_suspicious"
        result_data["verification_method"] = "ml_tamper"
        result_data["confidence"] = "medium"
    else:
        result_data["matched"] = False
        result_data["status"] = "external_media"
        result_data["verification_method"] = "none"
        result_data["confidence"] = "low"

    # ── Log verification ───────────────────────────────────────────────────────
    log_doc = {
        "verification_id": str(uuid.uuid4()),
        "admin_user_id": current_user["user_id"],
        "uploaded_hash": sha256_hash,
        "verification_method": result_data["verification_method"],
        "match_found": result_data["matched"],
        "watermark_matched": result_data["watermark_matched"],
        "hash_matched": result_data["hash_matched"],
        "similarity_matched": result_data["similarity_matched"],
        "similarity_score": result_data["similarity_score"],
        "similarity_matched_media_id": similarity_matched_media_id,
        # Phase 5
        "tamper_probability": result_data["tamper_probability"],
        "final_verdict": result_data["final_verdict"],
        "confidence_score": result_data["confidence_score"],
        "risk_level": result_data["risk_level"],
        "matched_user_id": result_data.get("original_user_id"),
        "matched_media_id": result_data.get("original_media_id"),
        "verified_at": verified_at,
    }
    await db.verification_logs.insert_one(log_doc)

    try:
        os.remove(temp_path)
    except Exception:
        pass

    return result_data
