
ZERO_WIDTH_0 = '\u200B'  # Zero Width Space   → bit '0'
ZERO_WIDTH_1 = '\u200C'  # Zero Width Non-Joiner → bit '1'

# Sentinel: 8 zero-width chars that signal the end of embedded data
SENTINEL_BITS = '00000000'  # 8 bits of 0 (null byte as terminator)
SENTINEL_ZW   = ZERO_WIDTH_0 * 8


def embed_text_watermark(file_path: str, secret_data: str) -> str:
    """
    Embeds secret_data into a text file using zero-width Unicode characters.
    Format: [zero-width watermark bits][SENTINEL = 8x ZW_0][visible content]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert secret to bits (byte-by-byte, big-endian, 8 bits per byte)
    bits = []
    for byte in secret_data.encode('utf-8'):
        for i in range(7, -1, -1):
            bits.append('1' if (byte >> i) & 1 else '0')
    bit_str = ''.join(bits)

    # Build zero-width watermark string + sentinel
    watermark_zw = ''
    for bit in bit_str:
        watermark_zw += ZERO_WIDTH_1 if bit == '1' else ZERO_WIDTH_0
    watermark_zw += SENTINEL_ZW  # null-byte sentinel marks end

    new_content = watermark_zw + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return file_path


def extract_text_watermark(file_path: str):
    """
    Extract watermark from a text file embedded via embed_text_watermark.
    Returns the secret string if found, else None.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        extracted_bits = []

        for char in content:
            if char == ZERO_WIDTH_0:
                extracted_bits.append('0')
            elif char == ZERO_WIDTH_1:
                extracted_bits.append('1')
            else:
                # First non-zero-width character: watermark block ended
                break

        if not extracted_bits:
            return None

        # Strip trailing sentinel bytes (groups of 8 zeros at the end)
        bit_str = ''.join(extracted_bits)

        # Remove trailing zero bytes (sentinel) – anything past the last non-zero byte
        # Work in 8-bit chunks and drop trailing null bytes
        byte_chunks = [bit_str[i:i+8] for i in range(0, len(bit_str), 8)]
        # Remove incomplete trailing chunk
        byte_chunks = [c for c in byte_chunks if len(c) == 8]
        # Remove trailing null bytes (sentinel)
        while byte_chunks and byte_chunks[-1] == '00000000':
            byte_chunks.pop()

        if not byte_chunks:
            return None

        # Decode bytes
        decoded_bytes = bytearray()
        for chunk in byte_chunks:
            decoded_bytes.append(int(chunk, 2))

        return decoded_bytes.decode('utf-8')

    except Exception as e:
        print(f"[extract_text_watermark] Error: {e}")
        return None
