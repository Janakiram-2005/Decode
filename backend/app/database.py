from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "media_verification_db")

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGODB_URL)
    
    try:
        await db.client[DB_NAME].media.create_index([("media_type", 1), ("uploaded_at", -1)])
        await db.client[DB_NAME].media.create_index("sha256_hash")
    except Exception as e:
        print(f"Index creation failed: {e}")
        
    print("Connected to MongoDB")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")

def get_database():
    return db.client[DB_NAME]
