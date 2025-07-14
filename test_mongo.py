import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    uri = "mongodb+srv://roshanerukulla555:Roshan123@cluster0.eizpdj0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = AsyncIOMotorClient(uri)
    try:
        dbs = await client.list_database_names()
        print("✅ MongoDB Connected:", dbs)
    except Exception as e:
        print("❌ MongoDB Error:", e)

asyncio.run(test())
