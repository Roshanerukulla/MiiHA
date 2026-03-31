from app.db.mongodb import db
from app.models.user import UserCreate
from app.utils.hash_utils import hash_password
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_user(user_data: UserCreate) -> str:
    user_dict = user_data.model_dump()  # .dict() is deprecated in Pydantic v2

    existing_user = await db.users.find_one({"email": user_dict["email"]})
    if existing_user:
        raise ValueError("Email already registered")

    user_dict["hashed_password"] = hash_password(user_dict.pop("password"))

    result = await db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)
    logger.info(f"New user registered: {user_dict['email']}")
    return user_id
