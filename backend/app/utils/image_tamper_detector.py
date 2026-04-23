"""
utils/image_tamper_detector.py
Phase 5 — Image Tamper Detection (heuristic + optional PyTorch).

Strategy:
  1. Run a fast heuristic check (noise analysis, edge irregularity, JPEG artifact
     asymmetry) that works without any trained model.
  2. Optionally load a PyTorch MobileNetV2 model (model.pth) if it exists.
     When the model file is absent the module falls back gracefully to heuristics.

The returned tamper_probability (0.0–1.0) represents how likely the image
has been modified / tampered with.
"""

from __future__ import annotations
import os
import io
import math

from PIL import Image, ImageFilter, ImageStat

# Path to the optional trained model file (saved next to this module)
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "model.pth")
_model = None          # populated once at first call
_model_loaded = False  # sentinel so we only try to load once


def _try_load_model():
    """
    Attempt to load the PyTorch model once. Sets globals _model / _model_loaded.
    Silently degrades if torch or the weights file is unavailable.
    """
    global _model, _model_loaded
    if _model_loaded:
        return
    _model_loaded = True  # mark regardless of outcome

    model_path = os.path.abspath(_MODEL_PATH)
    if not os.path.exists(model_path):
        print("[tamper] model.pth not found – using heuristic mode only.")
        return

    try:
        import torch
        import torchvision.models as models

        net = models.mobilenet_v2(weights=None)
        # Replace classifier head: 2 classes (authentic / tampered)
        net.classifier[1] = torch.nn.Linear(net.last_channel, 2)
        net.load_state_dict(torch.load(model_path, map_location="cpu"))
        net.eval()
        _model = net
        print("[tamper] Loaded PyTorch tamper model from model.pth")
    except Exception as exc:
        print(f"[tamper] Could not load PyTorch model ({exc}) – heuristic mode.")


# ── Heuristic Analysis ─────────────────────────────────────────────────────────

def _heuristic_tamper_score(image_path: str) -> float:
    """
    Fast, dependency-light heuristic tamper estimate.

    Checks:
      • Noise uniformity  – heavy compression / re-encoding raises noise.
      • Edge sharpness    – copy-paste regions often have uncharacteristically
                           sharp or blurred boundaries.
      • Chroma asymmetry  – channel std-dev imbalance can reveal JPEG splicing.

    Returns a probability in [0.0, 1.0].
    """
    try:
        img = Image.open(image_path).convert("RGB")
        # Limit memory – downsample large images for analysis
        max_side = 512
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side), Image.LANCZOS)

        stat = ImageStat.Stat(img)
        r_std, g_std, b_std = stat.stddev

        # Metric 1: channel imbalance – tampered / spliced images often have
        # unusual chroma balance after re-encoding
        mean_std = (r_std + g_std + b_std) / 3.0
        channel_imbalance = max(abs(r_std - mean_std), abs(g_std - mean_std), abs(b_std - mean_std))
        chroma_score = min(channel_imbalance / 30.0, 1.0)   # normalise to [0,1]

        # Metric 2: edge noise – apply edge detection and measure residual
        edges = img.filter(ImageFilter.FIND_EDGES).convert("L")
        edge_stat = ImageStat.Stat(edges)
        edge_mean = edge_stat.mean[0]  # 0 = flat, high = lots of edges
        edge_score = min(edge_mean / 80.0, 1.0)

        # Metric 3: overall brightness variance anomaly
        gray = img.convert("L")
        gray_stat = ImageStat.Stat(gray)
        brightness_var = gray_stat.var[0]
        # Very low or very high variance can indicate manipulation
        variance_score = 0.0
        if brightness_var < 200:          # nearly uniform – suspicious
            variance_score = 0.6
        elif brightness_var > 8000:       # extremely noisy
            variance_score = 0.5

        # Weighted combination - adjusted for better sensitivity
        heuristic_prob = (
            chroma_score   * 0.40 +
            edge_score     * 0.40 +
            variance_score * 0.20
        )
        return round(min(heuristic_prob, 1.0), 4)

    except Exception as exc:
        print(f"[tamper] Heuristic analysis failed: {exc}")
        return 0.0


# ── PyTorch Inference ──────────────────────────────────────────────────────────

def _pytorch_tamper_score(image_path: str) -> float | None:
    """
    Run inference using the loaded PyTorch model.
    Returns probability of class 1 (tampered) or None on failure.
    """
    if _model is None:
        return None
    try:
        import torch
        from torchvision import transforms

        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225]),
        ])

        img = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0)   # batch dim

        with torch.no_grad():
            logits = _model(tensor)
            probs = torch.softmax(logits, dim=1)
            tamper_prob = probs[0][1].item()

        return round(tamper_prob, 4)
    except Exception as exc:
        print(f"[tamper] PyTorch inference failed: {exc}")
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_image_tamper(image_path: str) -> dict:
    """
    Main entry point.

    Returns:
        {
            "tamper_detected": bool,
            "tamper_probability": float,   # 0.0 – 1.0
            "method": "ml" | "heuristic"
        }

    Threshold: tamper_detected = True  when probability >= 0.55
    """
    _try_load_model()

    method = "heuristic"
    prob = _heuristic_tamper_score(image_path)

    # Prefer ML score when model is available
    ml_prob = _pytorch_tamper_score(image_path)
    if ml_prob is not None:
        # Blend: 70% ML, 30% heuristic for robustness
        prob = round(ml_prob * 0.70 + prob * 0.30, 4)
        method = "ml"

    tamper_detected = prob >= 0.55

    return {
        "tamper_detected": tamper_detected,
        "tamper_probability": prob,
        "method": method,
    }
