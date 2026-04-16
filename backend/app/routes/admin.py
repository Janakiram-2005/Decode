from fastapi import APIRouter, HTTPException, status, Depends
from app.database import get_database
from app.routes.auth import get_current_user
from app.models import MediaResponse
from typing import List

router = APIRouter()


def _require_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )


@router.get("/media", response_model=List[MediaResponse])
async def get_all_media(current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    db = get_database()

    cursor = db.media.find().sort("uploaded_at", -1)
    media_list = await cursor.to_list(length=1000)

    # Enrich with uploader email via a single batched user lookup
    user_ids = list(set(m["user_id"] for m in media_list if "user_id" in m))
    users_cursor = db.users.find({"user_id": {"$in": user_ids}})
    users_map = {u["user_id"]: u["email"] async for u in users_cursor}

    for media in media_list:
        if media.get("user_id") in users_map:
            media["uploader_email"] = users_map[media["user_id"]]

    return media_list


@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    """Return high-level statistics for the Admin Dashboard."""
    _require_admin(current_user)
    db = get_database()

    total_media     = await db.media.count_documents({})
    total_images    = await db.media.count_documents({"media_type": "image"})
    total_texts     = await db.media.count_documents({"media_type": "text"})
    total_wm        = await db.media.count_documents({"watermark_present": True})
    total_verif     = await db.verification_logs.count_documents({})

    # Risk breakdown (Phase 5)
    risk_low    = await db.verification_logs.count_documents({"risk_level": "Low"})
    risk_medium = await db.verification_logs.count_documents({"risk_level": "Medium"})
    risk_high   = await db.verification_logs.count_documents({"risk_level": "High"})

    # Verdict breakdown
    verdict_counts = {}
    for verdict in ["Verified User", "Identical Reupload", "Derived Media",
                    "Tampered Suspicious", "External Media"]:
        verdict_counts[verdict] = await db.verification_logs.count_documents(
            {"final_verdict": verdict}
        )

    return {
        "total_media": total_media,
        "total_images": total_images,
        "total_texts": total_texts,
        "watermarked": total_wm,
        "total_verifications": total_verif,
        "risk_breakdown": {"Low": risk_low, "Medium": risk_medium, "High": risk_high},
        "verdict_breakdown": verdict_counts,
    }
