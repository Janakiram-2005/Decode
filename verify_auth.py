import requests
import uuid

BASE_URL = "http://localhost:8000/api"

def test_auth():
    email = f"test_{uuid.uuid4()}@example.com"
    password = "testpassword123"
    
    print(f"Testing with Email: {email}")
    
    # 1. Register
    print("1. Testing Registration...")
    reg_response = requests.post(f"{BASE_URL}/register", json={
        "email": email,
        "password": password
    })
    
    if reg_response.status_code == 200:
        print("   Registration SUCCESS")
    else:
        print(f"   Registration FAILED: {reg_response.text}")
        return

    # 2. Login
    print("2. Testing Login...")
    login_response = requests.post(f"{BASE_URL}/login", data={
        "username": email,
        "password": password
    })
    
    if login_response.status_code == 200:
        print("   Login SUCCESS")
        print(f"   Token: {login_response.json().get('access_token')[:20]}...")
    else:
        print(f"   Login FAILED: {login_response.status_code} {login_response.text}")

if __name__ == "__main__":
    try:
        test_auth()
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Is the backend server running on port 8000?")
