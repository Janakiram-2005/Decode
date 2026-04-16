"""
utils/image_similarity.py
Phase 4 — Image Similarity (pHash)
"""
from PIL import Image
import imagehash

def calculate_image_phash(image_file) -> str:
    """
    Calculate perceptual hash (pHash) of an image.
    Accepts a file path (str) OR a file-like object (BytesIO).
    Returns the hex string of the pHash, or None on failure.
    """
    try:
        if isinstance(image_file, str):
            image = Image.open(image_file)
        else:
            image = Image.open(image_file)
        phash = imagehash.phash(image)
        return str(phash)
    except Exception as e:
        print(f"[similarity] pHash error: {e}")
        return None

def calculate_phash_similarity(hash1_str: str, hash2_str: str) -> float:
    """
    Compare two pHash hex strings.
    Returns similarity percentage 0-100.
    Threshold for 'similar': >= 85%  (hamming distance <= ~9 out of 64 bits)
    """
    if not hash1_str or not hash2_str:
        return 0.0
    try:
        hash1 = imagehash.hex_to_hash(hash1_str)
        hash2 = imagehash.hex_to_hash(hash2_str)
        distance = hash1 - hash2
        similarity = max(0.0, (1.0 - distance / 64.0) * 100.0)
        return round(similarity, 2)
    except Exception as e:
        print(f"[similarity] pHash compare error: {e}")
        return 0.0

def find_best_image_match(query_phash: str, candidates: list, threshold: float = 92.0):
    """
    Given a query pHash string and a list of DB docs (each with 'phash' and 'media_id'),
    returns (best_doc, best_score) if any candidate exceeds the threshold, else (None, 0).
    Limited to top 100 candidates for performance.
    """
    best_score = 0.0
    best_doc = None
    for doc in candidates[:100]:
        stored_phash = doc.get("phash")
        if not stored_phash:
            continue
        score = calculate_phash_similarity(query_phash, stored_phash)
        if score > best_score:
            best_score = score
            best_doc = doc
    if best_score >= threshold:
        return best_doc, best_score
    return None, best_score
