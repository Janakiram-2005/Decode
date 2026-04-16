"""
Tests both layers of the new verify logic:
- Layer 1: watermark extraction + decrypt
- Layer 2: hash match (both original_sha256 AND sha256_hash)

Run: venv\Scripts\python.exe test_both_layers.py
"""
import sys, os, asyncio, hashlib, shutil, uuid
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("ENCRYPTION_KEY", "4d6c3f8a1b9e2c7f5a3d0e8b4c6f2a9d1e7b3c5f0a2d4e6b8c1f3a5d7e9b0c2")
from dotenv import load_dotenv; load_dotenv()

from PIL import Image
import numpy as np
from app.utils.encryption import encrypt_user_id, decrypt_token
from app.utils.image_watermark import embed_image_watermark, extract_image_watermark

P = lambda ok, msg: print(f"  {'[PASS]' if ok else '[FAIL]'} {msg}")

async def main():
    from app.database import connect_to_mongo, get_database
    await connect_to_mongo()
    db = get_database()

    # ── Setup: create a fake user + media doc with original_sha256 ─────────────
    fake_user_id = str(uuid.uuid4())
    fake_media_id = str(uuid.uuid4())

    # Create a test 100x100 image
    img_arr = (np.random.randint(100, 200, (100, 100, 3))).astype(np.uint8)
    orig_path = f"uploads/temp_verify/_test_orig_{fake_media_id}.png"
    wm_path   = f"uploads/temp_verify/_test_wm_{fake_media_id}.png"
    Image.fromarray(img_arr, 'RGB').save(orig_path)

    # Hash original
    with open(orig_path, 'rb') as f:
        original_sha256 = hashlib.sha256(f.read()).hexdigest()

    # Embed watermark
    token = encrypt_user_id(fake_user_id)
    shutil.copy2(orig_path, wm_path)
    final_wm_path = embed_image_watermark(wm_path, token)

    # Hash watermarked
    with open(final_wm_path, 'rb') as f:
        wm_sha256 = hashlib.sha256(f.read()).hexdigest()

    # Insert fake media doc
    await db.media.delete_many({"media_id": fake_media_id})  # cleanup
    await db.media.insert_one({
        "media_id": fake_media_id,
        "user_id": fake_user_id,
        "media_type": "image",
        "sha256_hash": wm_sha256,
        "original_sha256": original_sha256,
        "watermark_present": True,
    })

    print(f"\n=== TEST A: Hash of ORIGINAL (pre-watermark) file matches via $or ===")
    match = await db.media.find_one({"$or": [
        {"sha256_hash": original_sha256},
        {"original_sha256": original_sha256}
    ]})
    P(match is not None, f"Find original by original_sha256 -> {'FOUND: ' + str(match['media_id']) if match else 'NOT FOUND'}")

    print(f"\n=== TEST B: Hash of WATERMARKED file matches via $or ===")
    match2 = await db.media.find_one({"$or": [
        {"sha256_hash": wm_sha256},
        {"original_sha256": wm_sha256}
    ]})
    P(match2 is not None, f"Find watermarked by sha256_hash -> {'FOUND' if match2 else 'NOT FOUND'}")

    print(f"\n=== TEST C: Watermark extraction from watermarked PNG ===")
    extracted = extract_image_watermark(final_wm_path)
    P(extracted is not None, f"Watermark extracted: {str(extracted)[:40] if extracted else 'None'}...")
    if extracted:
        decrypted = decrypt_token(extracted)
        P(decrypted == fake_user_id, f"Decrypted user_id matches: {decrypted}")

    # Cleanup
    await db.media.delete_one({"media_id": fake_media_id})
    for p in [orig_path, final_wm_path]:
        if os.path.exists(p): os.remove(p)

    print("\n[DONE]")

asyncio.run(main())
