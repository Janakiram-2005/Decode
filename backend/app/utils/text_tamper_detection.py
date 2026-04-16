"""
utils/text_tamper_detection.py
Phase 5 — Text Modification / Tamper Detection.

Detects structural and semantic changes in text documents using:
  1. TF-IDF Cosine Similarity (always available via scikit-learn)
  2. Sentence-Transformers (MiniLM) when installed – much richer semantic check.

A high modification_score indicates the text has been substantially altered.
"""

from __future__ import annotations
from difflib import SequenceMatcher


# ── Sentence-Transformers (optional) ──────────────────────────────────────────

_st_model = None
_st_loaded = False


def _try_load_sentence_model():
    """Load MiniLM sentence-transformer once; degrades silently if unavailable."""
    global _st_model, _st_loaded
    if _st_loaded:
        return
    _st_loaded = True
    try:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[text_tamper] Loaded sentence-transformer model (MiniLM-L6-v2).")
    except Exception as exc:
        print(f"[text_tamper] sentence-transformers not available ({exc}) – using TF-IDF.")


# ── Core comparison helpers ────────────────────────────────────────────────────

def _tfidf_similarity(text_a: str, text_b: str) -> float:
    """Return cosine similarity 0–1 using TF-IDF."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vec = TfidfVectorizer(stop_words="english", min_df=1)
        mat = vec.fit_transform([text_a, text_b])
        return float(cosine_similarity(mat[0:1], mat[1:2]).flatten()[0])
    except Exception:
        return SequenceMatcher(None, text_a, text_b).ratio()


def _semantic_similarity(text_a: str, text_b: str) -> float:
    """Return cosine similarity 0–1 using sentence embeddings."""
    if _st_model is None:
        return _tfidf_similarity(text_a, text_b)
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        embs = _st_model.encode([text_a, text_b], convert_to_numpy=True)
        sim = cosine_similarity(embs[0:1], embs[1:2]).flatten()[0]
        return float(sim)
    except Exception as exc:
        print(f"[text_tamper] Semantic similarity failed: {exc}")
        return _tfidf_similarity(text_a, text_b)


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_text_tamper(original_text: str, query_text: str) -> dict:
    """
    Compare a query document against its suspected original.

    Args:
        original_text: Text stored in the database for the matched document.
        query_text:    Text extracted from the uploaded suspicious file.

    Returns:
        {
            "modification_score": float,  # 0.0 = identical, 1.0 = completely different
            "tamper_detected": bool,      # True when modification_score >= 0.35
            "method": "semantic" | "tfidf"
        }

    Threshold: tamper_detected = True when modification_score >= 0.35
    """
    _try_load_sentence_model()

    if not original_text or not query_text:
        return {"modification_score": 0.0, "tamper_detected": False, "method": "none"}

    if _st_model is not None:
        similarity = _semantic_similarity(original_text, query_text)
        method = "semantic"
    else:
        similarity = _tfidf_similarity(original_text, query_text)
        method = "tfidf"

    # modification_score is the inverse of similarity
    modification_score = round(1.0 - similarity, 4)
    tamper_detected = modification_score >= 0.35

    return {
        "modification_score": modification_score,
        "tamper_detected": tamper_detected,
        "method": method,
    }
