from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = "mongodb://127.0.0.1:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client["neptune-ai"]
users_collection = db["users"]
sessions_collection = db["sessions"]