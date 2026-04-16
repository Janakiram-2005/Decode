"""
routes/report.py
Phase 5+ — Downloadable PDF Verification Report.
POST /api/report/generate
Body: JSON matching VerificationResponse (result from /api/verify)
Returns: PDF file as attachment.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.routes.auth import get_current_user
from datetime import datetime
import io

router = APIRouter()


def _require_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")


@router.post("/generate")
async def generate_report(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a PDF forensic analysis report from a verification result.
    Accepts the full JSON body returned by /api/verify.
    """
    _require_admin(current_user)

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # ── Header ────────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 12, "FORENSIC VERIFICATION REPORT", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, "Traceable Media Verification System", ln=True, align="C")
        pdf.cell(0, 6, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", ln=True, align="C")
        pdf.ln(8)

        # ── Divider ───────────────────────────────────────────────────────────
        pdf.set_draw_color(200, 200, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        def section_header(title: str):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(40, 60, 140)
            pdf.cell(0, 8, title, ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)

        def row(label: str, value: str, color=None):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(60, 7, label + ":", ln=False)
            pdf.set_font("Helvetica", "", 10)
            if color:
                pdf.set_text_color(*color)
            else:
                pdf.set_text_color(20, 20, 20)
            pdf.cell(0, 7, str(value or "—"), ln=True)

        def bool_icon(val: bool) -> str:
            return "DETECTED" if val else "NOT FOUND"

        # ── Final Verdict ─────────────────────────────────────────────────────
        section_header("FINAL VERDICT")
        verdict       = data.get("final_verdict", "Unknown")
        risk_level    = data.get("risk_level", "Unknown")
        conf_score    = data.get("confidence_score")
        verified_at   = data.get("verified_at", "")

        verdict_color = (
            (20, 160, 80)  if verdict == "Verified User"       else
            (30, 100, 200) if verdict == "Identical Reupload"  else
            (200, 120, 20) if verdict == "Derived Media"       else
            (200, 40, 40)  if verdict == "Tampered Suspicious" else
            (140, 140, 40)
        )
        risk_color = (
            (20, 160, 80)  if risk_level == "Low"    else
            (200, 120, 20) if risk_level == "Medium" else
            (200, 40, 40)
        )

        row("Verdict",          verdict, verdict_color)
        row("Risk Level",       risk_level, risk_color)
        row("Confidence Score", f"{conf_score}%" if conf_score is not None else "N/A")
        row("Verified At",      verified_at)
        pdf.ln(4)

        # ── Layer 1: Watermark ─────────────────────────────────────────────────
        section_header("LAYER 1 — Watermark Check")
        wm = data.get("watermark_matched", False)
        row("Status",           bool_icon(wm), (20,160,80) if wm else (150,150,150))
        row("Uploader Email",   data.get("uploader_email"))
        row("User ID",          data.get("original_user_id"))
        row("WM Version",       data.get("watermark_version"))
        pdf.ln(4)

        # ── Layer 2: Hash ──────────────────────────────────────────────────────
        section_header("LAYER 2 — Cryptographic Hash (SHA-256)")
        hm = data.get("hash_matched", False)
        row("Status",           "MATCH FOUND" if hm else "NO MATCH",
            (30,100,200) if hm else (180,50,50))
        row("Media ID",         data.get("original_media_id"))
        row("Upload Date",      str(data.get("original_upload_date") or "—"))
        row("SHA-256",          data.get("hashed", "")[:48] + "..." if data.get("hashed") else "—")
        pdf.ln(4)

        # ── Layer 3: Similarity ────────────────────────────────────────────────
        section_header("LAYER 3 — Perceptual / Semantic Similarity")
        sm = data.get("similarity_matched", False)
        sim_score = data.get("similarity_score", 0)
        row("Status",           "SIMILAR FOUND" if sm else "NO SIMILAR",
            (200, 120, 20) if sm else (150,150,150))
        row("Similarity Score", f"{sim_score}%")
        row("Matched Media ID", data.get("similarity_matched_media_id"))
        pdf.ln(4)

        # ── Layer 4: ML Tamper ─────────────────────────────────────────────────
        section_header("LAYER 4 — ML Tamper Detection")
        td = data.get("tamper_detected", False)
        tp = data.get("tamper_probability", 0)
        row("Status",        "TAMPERED" if td else "AUTHENTIC",
            (200,40,40) if td else (20,160,80))
        row("Tamper Probability", f"{round(float(tp)*100, 1)}%")
        row("Detection Method",   data.get("tamper_method", "heuristic"))
        pdf.ln(4)

        # ── Layer 5: Risk Engine ───────────────────────────────────────────────
        section_header("LAYER 5 — Risk Score Aggregation")
        row("Formula",
            "WM(50%) + Hash(30%) + Similarity(10%) + ML(10%)")
        row("Final Confidence Score", f"{conf_score}%" if conf_score is not None else "N/A")
        row("Risk Level",            risk_level, risk_color)
        pdf.ln(4)

        # ── Footer ─────────────────────────────────────────────────────────────
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(0, 6,
            "This report is auto-generated by the Traceable Media Verification System. "
            "For official use only.",
            ln=True, align="C")

        # ── Output as streaming PDF ────────────────────────────────────────────
        pdf_bytes = pdf.output()
        buffer = io.BytesIO(bytes(pdf_bytes))
        buffer.seek(0)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"verification_report_{ts}.pdf"

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF generation library not installed. Run: pip install fpdf2"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
