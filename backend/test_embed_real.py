"""Quick test: embed watermark in a real JPEG from uploads/ to see what error occurs."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("ENCRYPTION_KEY", "4d6c3f8a1b9e2c7f5a3d0e8b4c6f2a9d1e7b3c5f0a2d4e6b8c1f3a5d7e9b0c2")
from dotenv import load_dotenv; load_dotenv()

from app.utils.encryption import encrypt_user_id
from app.utils.image_watermark import embed_image_watermark, extract_image_watermark
from app.utils.encryption import decrypt_token
import shutil, uuid

# Use the first .jpg we found
src = r"uploads/images/fac943bb-1de3-4141-aef9-74754ed5222a.jpg"
dst = r"uploads/images/_test_wm_copy.jpg"

shutil.copy2(src, dst)
fake_uid = str(uuid.uuid4())
token = encrypt_user_id(fake_uid)

print(f"Token length: {len(token)} chars, bits needed: {(len(token)+5)*8}")

try:
    result_path = embed_image_watermark(dst, token)
    print(f"[OK] Embedded! Saved to: {result_path}")
    # Now extract
    extracted = extract_image_watermark(result_path)
    if extracted:
        decrypted = decrypt_token(extracted)
        if decrypted == fake_uid:
            print(f"[PASS] Round-trip PASS: {decrypted}")
        else:
            print(f"[FAIL] Decrypted={decrypted}, Expected={fake_uid}")
    else:
        print(f"[FAIL] Extraction returned None")
    # Cleanup
    if os.path.exists(result_path): os.remove(result_path)
except Exception as e:
    import traceback
    print(f"[FAIL] Exception during embed: {e}")
    traceback.print_exc()
    if os.path.exists(dst): os.remove(dst)
