"""
Debug script: diagnose verify failures by checking DB vs disk.
Run: venv\Scripts\python.exe debug_verify.py
"""
import sys
import os
import hashlib
import asyncio

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("ENCRYPTION_KEY", "4d6c3f8a1b9e2c7f5a3d0e8b4c6f2a9d1e7b3c5f0a2d4e6b8c1f3a5d7e9b0c2")
from dotenv import load_dotenv
load_dotenv()

from app.utils.image_watermark import extract_image_watermark
from app.utils.encryption import decrypt_token

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

async def main():
    from app.database import connect_to_mongo, get_database
    await connect_to_mongo()
    db = get_database()

    cursor = db.media.find({}, {"_id": 0}).sort("uploaded_at", -1).limit(5)
    docs = await cursor.to_list(length=5)

    if not docs:
        print(f"{FAIL} No uploads found in DB!")
        return

    print(f"\n{INFO} Last {len(docs)} upload(s) in DB:\n")
    for i, doc in enumerate(docs):
        fp = doc.get("file_path", "?")
        exists = os.path.exists(fp) if fp else False
        wm = doc.get("watermark_present", False)
        print(f"  [{i+1}] media_id={doc.get('media_id','?')}")
        print(f"       file_path={fp}")
        print(f"       exists={exists}, watermark_present={wm}")
        print(f"       sha256={doc.get('sha256_hash','?')[:20]}...")
        enc = doc.get('encrypted_token')
        print(f"       encrypted_token={'(stored) ' + str(enc)[:40] if enc else 'NONE (not stored)'}")
        print()

    for doc in docs:
        fp = doc.get("file_path")
        if not fp or not os.path.exists(fp):
            print(f"{WARN} File not on disk: {fp} -- skipped")
            continue

        print("=" * 60)
        print(f"{INFO} Testing: {os.path.basename(fp)}")

        # --- Hash check ---
        stored_hash = doc.get("sha256_hash", "")
        h = hashlib.sha256()
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        computed_hash = h.hexdigest()

        if computed_hash == stored_hash:
            print(f"  Hash:    {PASS} SHA-256 matches DB")
        else:
            print(f"  Hash:    {FAIL} MISMATCH!")
            print(f"    DB   : {stored_hash}")
            print(f"    Disk : {computed_hash}")

        # --- Watermark ---
        media_type = doc.get("media_type", "unknown")
        if media_type == "image":
            extracted = extract_image_watermark(fp)
            if extracted:
                print(f"  WM Ext: {PASS} Extracted {len(extracted)} chars")
                decrypted = decrypt_token(extracted)
                if decrypted:
                    print(f"  WM Dec: {PASS} user_id={decrypted}")
                    try:
                        import uuid
                        uuid.UUID(decrypted)
                        print(f"  UUID:   {PASS} Valid UUID")
                    except Exception:
                        print(f"  UUID:   {FAIL} NOT a valid UUID -- decryption garbage!")
                else:
                    print(f"  WM Dec: {FAIL} decrypt_token() returned None")
                    print(f"    Raw extracted (first 80 chars): {extracted[:80]}")
            else:
                print(f"  WM Ext: {FAIL} No watermark found in image")
                from PIL import Image
                img = Image.open(fp).convert('RGB')
                w, h2 = img.size
                channels = w * h2 * 3
                stored_enc = doc.get("encrypted_token", "")
                required_bits = (len(stored_enc) + 5) * 8
                print(f"    Image {w}x{h2}, channels={channels}, bits_needed~{required_bits}")
                if channels < required_bits:
                    print(f"    --> {FAIL} IMAGE TOO SMALL to hold watermark!")
                else:
                    print(f"    --> Image large enough. Watermark likely missing from embedding.")
        elif media_type == "text":
            from app.utils.text_watermark import extract_text_watermark
            extracted = extract_text_watermark(fp)
            if extracted:
                print(f"  WM Ext: {PASS} Extracted {len(extracted)} chars")
                decrypted = decrypt_token(extracted)
                if decrypted:
                    print(f"  WM Dec: {PASS} user_id={decrypted}")
                else:
                    print(f"  WM Dec: {FAIL} decrypt returned None")
            else:
                print(f"  WM Ext: {FAIL} No watermark found in text file")

    print("\n" + "=" * 60)
    print(f"{INFO} Diagnosis complete.")

asyncio.run(main())
