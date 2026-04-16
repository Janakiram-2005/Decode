from PIL import Image
import numpy as np

DELIMITER = "#####"

def _str_to_bits(text: str) -> list:
    """Convert a string to a list of '0'/'1' bit characters, byte by byte."""
    result = []
    for char in text:
        byte_val = ord(char)
        for bit in range(7, -1, -1):
            result.append('1' if (byte_val >> bit) & 1 else '0')
    return result

def _bits_to_str(bits: list) -> str:
    """Convert a list of '0'/'1' bit characters back to a string."""
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            break
        val = int(''.join(byte_bits), 2)
        try:
            chars.append(chr(val))
        except Exception:
            break
    return ''.join(chars)


def embed_image_watermark(image_path: str, secret_data: str) -> str:
    """
    Embed secret_data into image using pixel LSB steganography.
    Always saves as PNG (lossless) to preserve LSB bits.
    Returns the final saved path (may change from .jpg/.jpeg to .png).
    """
    import os

    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    pixels = np.array(img, dtype=np.uint8)

    # Data to embed: secret + delimiter
    payload = secret_data + DELIMITER
    bits = _str_to_bits(payload)

    total_bits = len(bits)
    total_channels = width * height * 3  # R, G, B channels

    if total_bits > total_channels:
        raise ValueError(
            f"Image too small: need {total_bits} bits but only {total_channels} channels available."
        )

    # Flatten to a 1D array of uint8 channel values
    flat = pixels.flatten().astype(np.int32)  # use int32 to avoid uint8 overflow

    for i, bit in enumerate(bits):
        # Clear LSB then set it: use 0xFE mask (not ~1 which is -2 in Python)
        flat[i] = (flat[i] & 0xFE) | int(bit)

    # Reshape back and convert to uint8
    watermarked = flat.reshape(pixels.shape).astype(np.uint8)
    result_img = Image.fromarray(watermarked, 'RGB')

    # Always save as PNG (lossless)
    base, ext = os.path.splitext(image_path)
    save_path = base + '.png'

    if os.path.exists(image_path) and image_path != save_path:
        os.remove(image_path)  # Remove original JPEG

    result_img.save(save_path, format='PNG')
    return save_path


def extract_image_watermark(image_path: str):
    """
    Extract watermark from image by reading pixel LSBs.
    Returns the secret string if delimiter found, else None.
    """
    try:
        img = Image.open(image_path).convert('RGB')
        flat = np.array(img, dtype=np.uint8).flatten()

        extracted_bits = []
        extracted_chars = []

        for i, pixel_val in enumerate(flat):
            extracted_bits.append('1' if (pixel_val & 1) else '0')

            # Every 8 bits, decode a character
            if len(extracted_bits) % 8 == 0:
                byte_bits = extracted_bits[-8:]
                val = int(''.join(byte_bits), 2)
                try:
                    ch = chr(val)
                    extracted_chars.append(ch)
                except Exception:
                    extracted_chars.append('?')

                # Check for delimiter in the last 5 decoded characters
                if len(extracted_chars) >= len(DELIMITER):
                    tail = ''.join(extracted_chars[-len(DELIMITER):])
                    if tail == DELIMITER:
                        result = ''.join(extracted_chars[:-len(DELIMITER)])
                        return result

                # Safety limit: 20KB of extracted text is more than enough
                if len(extracted_chars) > 20000:
                    break

        return None

    except Exception as e:
        print(f"[extract_image_watermark] Error: {e}")
        return None
