import asyncio
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME", "media_verification_db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

async def seed_users():
    print(f"Connecting to MongoDB at {MONGODB_URL}...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]
    
    # Test Data
    users_to_create = [
        {
            "user_id": str(uuid.uuid4()),
            "email": "user@example.com",
            "password": "user123",
            "role": "user"
        },
        {
            "user_id": str(uuid.uuid4()),
            "email": "admin@example.com",
            "password": "admin123",
            "role": "admin"
        }
    ]
    
    for u_data in users_to_create:
        existing = await db.users.find_one({"email": u_data["email"]})
        if existing:
            print(f"User {u_data['email']} already exists. Skipping.")
            continue
        
        user_doc = {
            "user_id": u_data["user_id"],
            "email": u_data["email"],
            "password_hash": get_password_hash(u_data["password"]),
            "role": u_data["role"],
            "created_at": datetime.utcnow()
        }
        await db.users.insert_one(user_doc)
        print(f"Created {u_data['role']}: {u_data['email']} (Password: {u_data['password']})")

    print("Seeding complete.")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_users())
