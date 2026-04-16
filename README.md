# Traceable Media Verification System
**Phase 4: Similarity Detection Layer**

## Overview
A comprehensive forensic analysis and verification system designed to detect and trace digital media (images and text) using multiple layers of security and validation. Phase 4 introduces **Level 3 Similarity Detection**, ensuring robust coverage against cropped, resized, stripped, or paraphrased media.

## Architecture

* **Frontend**: React + Vite + Tailwind CSS
* **Backend**: FastAPI (Python)
* **Database**: MongoDB (motor, asyncio)

---

## 3-Layer Verification Protocol

When a file is uploaded for verification, it undergoes three comprehensive checks:

### ⚙️ Layer 1: Cryptographic Watermark
* **Images:** LSB (Least Significant Bit) Steganography is used to imperceptibly embed an AES-256 encrypted unique user/tracing token into the image pixels.
* **Text:** Invisibly embeds encrypted tracing zero-width characters into plain text.
* **Result:** Confirms direct ownership if the hidden watermark is fully recoverable.

### ⚙️ Layer 2: Secure Hashing
* Generate the SHA-256 hash of the media and check against the database of known registered media. 
* Automatically matches against both the *original file* hash and the *watermarked copy* hash.
* **Result:** Detects direct identical copies even if the embedded watermark has been accidentally stripped.

### ⚙️ Layer 3: Semantic/Perceptual Similarity (Phase 4)
* **Images:** Generates a **pHash (Perceptual Hash)** using `imagehash`. Calculates the Hamming distance across highly-indexed candidates.
* **Text:** Uses **TF-IDF Vectorization** (via `scikit-learn`) and computes **Cosine Similarity** against text repositories.
* **Result:** Detects structurally or contextually similar files (e.g., compressed images, cropped graphics, paraphrased text). A match is flagged when similarity thresholds > 85%.

---

## System Workflow
1. **Secure Upload:** Users upload digital media. The app securely watermarks the content with an AES token and simultaneously hashes it for verification.
2. **Analysis Interface:** Admins can scan dubious files using the Media Verification Lab.
3. **Multi-Step Animation:** Real-time feedback processes the forensic checks progressively layer-by-layer.
4. **Verdicts:** Direct Match (Watermark + Hash), Authentic Copy (Hash), Similar Media Found, or External Media.

## Performance Optimization
- **Perceptual Hashes pre-calculated** during upload to save processing time on verification.
- Search queries are optimized to **Limit the scope** to top 100 recent matching types.
- **MongoDB compound indexing:** Optimized retrieval using indexes on `media_type`, `uploaded_at`, and `sha256_hash`.

## Installation & Running
1. Start the React server (Vite): `cd frontend && npm install && npm run dev`
2. Start the FastAPI backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
