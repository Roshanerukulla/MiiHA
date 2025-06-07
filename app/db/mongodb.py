from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.database_name]

print("🧪 [DEBUG] MONGODB_URI:", settings.mongodb_uri)
print("🧪 [DEBUG] DATABASE_NAME:", settings.database_name)

# 🕵️ Add this line to see what databases exist
#import asyncio
#async def debug_connection():
 #   dbs = await client.list_database_names()
  #  print("✅ MongoDB Databases:", dbs)

#asyncio.get_event_loop().create_task(debug_connection())