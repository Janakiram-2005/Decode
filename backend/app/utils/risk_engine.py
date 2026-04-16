"""
utils/risk_engine.py
Phase 5 — Unified Risk Scoring Engine.
Combines Watermark (50%) + Hash (30%) + Similarity (10%) + ML Tamper (10%)
into a single confidence score and risk level verdict.
"""


def compute_risk_score(
    watermark_matched: bool,
    hash_matched: bool,
    similarity_score: float,   # 0–100
    tamper_probability: float, # 0.0–1.0  (0 = authentic, 1 = tampered)
) -> dict:
    """
    Compute a weighted risk / confidence score from all 4 verification layers.

    Weight distribution:
        Watermark  → 50%
        Hash       → 30%
        Similarity → 10%
        ML Tamper  → 10%

    Returns a dict with:
        confidence_score  (0–100, higher = more authentic / trustworthy)
        final_verdict     str
        risk_level        "Low" | "Medium" | "High"
    """
    wm_score   = 100.0 if watermark_matched else 0.0
    hash_score = 100.0 if hash_matched else 0.0
    sim_score  = float(similarity_score)                   # already 0-100
    ml_score   = (1.0 - float(tamper_probability)) * 100.0 # invert: authentic = high

    confidence_score = (
        wm_score   * 0.50 +
        hash_score * 0.30 +
        sim_score  * 0.10 +
        ml_score   * 0.10
    )
    confidence_score = round(min(max(confidence_score, 0.0), 100.0), 1)

    # ── Final Verdict ──────────────────────────────────────────────────────────
    if watermark_matched and hash_matched:
        final_verdict = "Verified User"
    elif watermark_matched:
        final_verdict = "Verified User"
    elif hash_matched:
        final_verdict = "Identical Reupload"
    elif similarity_score >= 92.0 and tamper_probability < 0.5:
        final_verdict = "Derived Media"
    elif tamper_probability >= 0.6:
        final_verdict = "Tampered Suspicious"
    else:
        final_verdict = "External Media"

    # ── Risk Level ─────────────────────────────────────────────────────────────
    if confidence_score >= 75:
        risk_level = "Low"
    elif confidence_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "confidence_score": confidence_score,
        "final_verdict": final_verdict,
        "risk_level": risk_level,
    }
