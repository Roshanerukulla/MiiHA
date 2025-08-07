# app/db/firestore_client.py

import os
from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient
from dotenv import load_dotenv

load_dotenv()

# 🔹 Synchronous Firestore client (used for regular DB access)
db = firestore.Client()

# 🔹 Asynchronous Firestore client (used in services like query_service.py)
async_db = AsyncClient()

# (Optional) Convenience access to collections
users_collection = db.collection("users")
chat_sessions_collection = db.collection("chat_sessions")
