import os
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

# Detect Cloud Run
if os.getenv("K_SERVICE"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/secret/miiha-service-account"
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

db = firestore.Client()
users_collection = db.collection("users")
chat_sessions_collection = db.collection("chat_sessions")
