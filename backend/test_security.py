from app.utils.security import get_password_hash, verify_password

try:
    print("Testing get_password_hash (Argon2)...")
    pwd = "testpassword123" + "verylongpassword" * 10
    print(f"Password length: {len(pwd)}")
    
    hashed = get_password_hash(pwd)
    print(f"Hash created: {hashed[:30]}...")
    
    print("Testing verify_password...")
    valid = verify_password(pwd, hashed)
    print(f"Verify result: {valid}")
    
    if valid:
        print("SUCCESS: Argon2 hashing working correctly!")
    else:
        print("FAILURE: Verification returned False")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
