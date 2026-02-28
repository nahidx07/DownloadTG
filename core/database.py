import firebase_admin
from firebase_admin import credentials, firestore
import logging
from core.config import FIREBASE_CREDS

logger = logging.getLogger(__name__)

# Firebase Initialize (একবারই হবে)
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDS)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Connected Successfully!")
except Exception as e:
    print(f"❌ Firebase Init Error: {e}")

async def save_user(user):
    """ইউজার ডাটা সেভ করার ফাংশন"""
    try:
        user_ref = db.collection("users").document(str(user.id))
        doc = user_ref.get()
        if not doc.exists:
            user_ref.set({
                "user_id": user.id,
                "username": user.username if user.username else "N/A",
                "first_name": user.first_name,
                "join_date": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"New user saved: {user.id}")
    except Exception as e:
        logger.error(f"Firestore Save Error: {e}")

async def get_all_users():
    """সব ইউজারের আইডি লিস্ট রিটার্ন করার ফাংশন (ব্রডকাস্টের জন্য)"""
    try:
        users_ref = db.collection("users").stream()
        # সব ডকুমেন্ট থেকে শুধু আইডিগুলো নিয়ে একটি লিস্ট তৈরি করা
        user_ids = [doc.id for doc in users_ref]
        return user_ids
    except Exception as e:
        logger.error(f"Firestore Fetch Error: {e}")
        return []
