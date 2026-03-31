from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.database_name]


async def check_connection() -> bool:
    """Ping MongoDB to verify the connection is reachable."""
    try:
        await client.admin.command("ping")
        logger.info("MongoDB connection verified")
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return False
