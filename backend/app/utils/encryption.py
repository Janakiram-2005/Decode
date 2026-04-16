import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

# Configuration
# Ensure you have a 32-byte key for AES-256
# In production, load this from a secure environment variable
DEFAULT_KEY = b'01234567890123456789012345678901' # Placeholder 32 bytes

def get_key():
    env_key = os.getenv("ENCRYPTION_KEY")
    if env_key:
        # Expecting hex or base64 key in env? Let's assume hex for now or raw bytes if possible.
        # Ideally, it should be 32 bytes.
        try:
            return bytes.fromhex(env_key)
        except:
             # Fallback if not hex
             return env_key.encode()[:32].ljust(32, b'0')
    return DEFAULT_KEY

def encrypt_user_id(user_id: str) -> str:
    key = get_key()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Pad data to 128-bit block size
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(user_id.encode()) + padder.finalize()
    
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    
    # Return as base64 (IV + Ciphertext)
    return base64.b64encode(iv + encrypted).decode('utf-8')

def decrypt_token(token: str) -> str:
    try:
        key = get_key()
        data = base64.b64decode(token)
        iv = data[:16]
        ciphertext = data[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        user_id = unpadder.update(padded_data) + unpadder.finalize()
        
        return user_id.decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None
