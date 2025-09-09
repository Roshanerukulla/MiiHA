import os
from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient
from dotenv import load_dotenv

load_dotenv()

# 🔹 Hardcode or pull project ID from env
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "iui-info-hcc-hci")

# Synchronous Firestore client
db = firestore.Client(project=PROJECT_ID)

# Asynchronous Firestore client
async_db = AsyncClient(project=PROJECT_ID)

# Optional collections
users_collection = db.collection("users")
chat_sessions_collection = db.collection("chat_sessions")

print(f"✅ Firestore connected to project: {PROJECT_ID}")
