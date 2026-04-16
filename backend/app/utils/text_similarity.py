"""
utils/text_similarity.py
Phase 4 — Text Similarity (TF-IDF + Cosine).
"""
from difflib import SequenceMatcher

def extract_raw_text(file_path: str) -> str:
    """Read and return the plain text content of a text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"[similarity] text read error: {e}")
        return ""

def compute_tfidf_similarity(target_text: str, corpus_texts: list) -> list:
    """
    Compare target_text against a list of corpus strings using TF-IDF + Cosine Similarity.
    Returns a list of similarity scores (0.0–1.0) aligned with corpus_texts.
    Falls back to SequenceMatcher if scikit-learn unavailable.
    """
    if not target_text or not corpus_texts:
        return [0.0] * len(corpus_texts)
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        all_docs = [target_text] + corpus_texts
        vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        tfidf_matrix = vectorizer.fit_transform(all_docs)
        # Compare first doc (target) against all others
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        return scores.tolist()
    except Exception as e:
        print(f"[similarity] TF-IDF failed ({e}), falling back to SequenceMatcher")
        return [
            SequenceMatcher(None, target_text, t).ratio() for t in corpus_texts
        ]

def find_best_text_match(target_text: str, candidates: list, threshold: float = 0.88):
    """
    Given target_text and a list of DB docs (each with 'extracted_text' and 'media_id'),
    returns (best_doc, best_score_percent) if any candidate exceeds the threshold, else (None, 0).
    Limited to top 100 candidates for performance.
    """
    candidates = [c for c in candidates[:100] if c.get("extracted_text")]
    if not candidates:
        return None, 0.0

    corpus_texts = [c["extracted_text"] for c in candidates]
    scores = compute_tfidf_similarity(target_text, corpus_texts)

    best_idx = int(max(range(len(scores)), key=lambda i: scores[i]))
    best_score = scores[best_idx]

    if best_score >= threshold:
        return candidates[best_idx], round(best_score * 100, 2)
    return None, round(best_score * 100, 2)

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Legacy: SequenceMatcher-based similarity. Returns 0-100."""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio() * 100.0
