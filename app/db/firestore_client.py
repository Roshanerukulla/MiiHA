# app/db/firestore_client.py

import os


# Connect to Firestore emulator locally
#os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
#os.environ["GOOGLE_CLOUD_PROJECT"] = "miiha-local"
# Use default credentials for Cloud Firestore (Cloud project must be set)
from google.cloud import firestore

db = firestore.Client(project="miiha-local")


users_collection = db.collection("users")
chat_sessions_collection = db.collection("chat_sessions")