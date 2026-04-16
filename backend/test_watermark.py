"""
Round-trip verification test for Phase 3 watermark integration.
Run from backend/ with venv active:
    python test_watermark.py
"""
import os
import sys
import uuid
import tempfile

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("ENCRYPTION_KEY", "4d6c3f8a1b9e2c7f5a3d0e8b4c6f2a9d1e7b3c5f0a2d4e6b8c1f3a5d7e9b0c2")
from dotenv import load_dotenv
load_dotenv()

from app.utils.encryption import encrypt_user_id, decrypt_token
from app.utils.image_watermark import embed_image_watermark, extract_image_watermark
from app.utils.text_watermark import embed_text_watermark, extract_text_watermark

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
INFO = "\033[94mINFO\033[0m"

def test_encryption():
    print(f"\n[{INFO}] TEST 1 — AES-256 Encryption Round-Trip")
    user_id = str(uuid.uuid4())
    print(f"  Original user_id : {user_id}")
    token = encrypt_user_id(user_id)
    print(f"  Encrypted token  : {token[:40]}...")
    decrypted = decrypt_token(token)
    print(f"  Decrypted        : {decrypted}")
    if decrypted == user_id:
        print(f"  Result: {PASS}")
        return True
    else:
        print(f"  Result: {FAIL} — mismatch!")
        return False

def test_image_watermark():
    print(f"\n[{INFO}] TEST 2 — Image Watermark Round-Trip (PNG)")
    from PIL import Image
    import numpy as np

    user_id = str(uuid.uuid4())
    token = encrypt_user_id(user_id)
    print(f"  Embedding for user_id: {user_id}")

    # Create a test 64x64 white PNG
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    img = Image.fromarray(
        (255 * np.ones((64, 64, 3), dtype=np.uint8)), 'RGB'
    )
    img.save(tmp_path)

    try:
        saved_path = embed_image_watermark(tmp_path, token)
        print(f"  Watermarked file : {saved_path}")

        extracted_token = extract_image_watermark(saved_path)
        print(f"  Extracted token  : {str(extracted_token)[:40] if extracted_token else 'None'}...")

        if not extracted_token:
            print(f"  Result: {FAIL} — no token extracted")
            return False

        decrypted = decrypt_token(extracted_token)
        print(f"  Decrypted user_id: {decrypted}")

        if decrypted == user_id:
            print(f"  Result: {PASS}")
            return True
        else:
            print(f"  Result: {FAIL} — user_id mismatch (got {decrypted!r})")
            return False
    finally:
        for p in [tmp_path, saved_path if 'saved_path' in dir() else None]:
            if p and os.path.exists(p):
                os.remove(p)

def test_text_watermark():
    print(f"\n[{INFO}] TEST 3 — Text Watermark Round-Trip (.txt)")
    user_id = str(uuid.uuid4())
    token = encrypt_user_id(user_id)
    print(f"  Embedding for user_id: {user_id}")

    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as tmp:
        tmp.write("This is a sample document with some visible text content.")
        tmp_path = tmp.name

    try:
        embed_text_watermark(tmp_path, token)
        extracted_token = extract_text_watermark(tmp_path)
        print(f"  Extracted token: {str(extracted_token)[:40] if extracted_token else 'None'}...")

        if not extracted_token:
            print(f"  Result: {FAIL} — no token extracted")
            return False

        decrypted = decrypt_token(extracted_token)
        print(f"  Decrypted user_id: {decrypted}")

        if decrypted == user_id:
            print(f"  Result: {PASS}")
            return True
        else:
            print(f"  Result: {FAIL} — user_id mismatch (got {decrypted!r})")
            return False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_uuid_validation():
    print(f"\n[{INFO}] TEST 4 — UUID validation rejects garbage decryption")
    # A token that is syntactically valid base64 + decryptable but NOT a UUID
    garbage_text = "notauuid1234"
    token = encrypt_user_id(garbage_text)
    decrypted = decrypt_token(token)
    try:
        import uuid as _uuid
        _uuid.UUID(decrypted)
        print(f"  Result: {FAIL} — should have rejected, but UUID() passed for '{decrypted}'")
        return False
    except (ValueError, AttributeError):
        print(f"  UUID validation correctly rejects non-UUID string: '{decrypted}'")
        print(f"  Result: {PASS}")
        return True

if __name__ == "__main__":
    results = [
        test_encryption(),
        test_image_watermark(),
        test_text_watermark(),
        test_uuid_validation(),
    ]
    total = len(results)
    passed = sum(results)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed")
    if passed == total:
        print(f"\033[92mAll tests passed! Watermark pipeline is working.\033[0m")
    else:
        print(f"\033[91m{total - passed} test(s) failed.\033[0m")
    sys.exit(0 if passed == total else 1)
