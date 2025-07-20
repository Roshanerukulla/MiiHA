import os
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

# app/db/firestore_client.py

db = firestore.Client()

users_collection = db.collection("users")
chat_sessions_collection = db.collection("chat_sessions")
