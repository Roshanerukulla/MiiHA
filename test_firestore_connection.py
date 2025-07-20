# test_firestore_connection.py
from app.db.firestore_client import db

def test_firestore():
    doc_ref = db.collection("test").document("ping")
    doc_ref.set({"status": "working"})

    doc = doc_ref.get()
    print("✅ Firestore Test:", doc.to_dict())

if __name__ == "__main__":
    test_firestore()
