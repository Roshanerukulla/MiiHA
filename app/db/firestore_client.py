import os
from google.cloud import firestore
from dotenv import load_dotenv

# Load environment variables from .env (if using)
load_dotenv()

# Point to the downloaded Firebase service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/secrets/miiha-key.json"

# Initialize Firestore client
db = firestore.Client()
users_collection = db.collection("users")
chat_sessions_collection = db.collection("chat_sessions")
