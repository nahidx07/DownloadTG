import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from core.config import FIREBASE_CREDS

# Firebase Initialize
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDS)
    firebase_admin.initialize_app(cred)

db = firestore.client()

async def save_user(user):
    user_ref = db.collection("users").document(str(user.id))
    doc = user_ref.get()
    if not doc.exists:
        user_ref.set({
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

async def get_all_users():
    users = db.collection("users").stream()
    return [user.id for user in users]
