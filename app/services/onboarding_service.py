# app/services/onboarding_service.py

from uuid import uuid4
from app.db.firestore_client import db  # using Firestore now
from app.models.user import UserCreate
from app.utils.hash_utils import hash_password
from google.cloud.exceptions import NotFound

async def create_user(user: UserCreate):
    user_dict = user.dict()
    user_dict["email"] = user_dict["email"].lower()

    # Check if user already exists
    existing_users = db.collection("users").where("email", "==", user_dict["email"]).limit(1).stream()
    if any(existing_users):
        raise ValueError("User already exists")

    # Generate short user_id and hash password
    user_id = uuid4().hex[:10]
    user_dict["user_id"] = user_id
    user_dict["hashed_password"] = hash_password(user_dict.pop("password"))

    # Store in Firestore with doc ID = user_id
    db.collection("users").document(user_id).set(user_dict)

    return user_id
