import firebase_admin
from firebase_admin import credentials, firestore
import json
import logging
from core.config import FIREBASE_CREDS

logger = logging.getLogger(__name__)

# Firebase Initialize
try:
    if not firebase_admin._apps:
        # সরাসরি ডিকশনারি থেকে ক্রেডেনশিয়াল নেওয়া
        cred = credentials.Certificate(FIREBASE_CREDS)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("✅ Firebase Connected Successfully!")
except Exception as e:
    logger.error(f"❌ Firebase Init Error: {e}")

async def save_user(user):
    try:
        user_ref = db.collection("users").document(str(user.id))
        doc = user_ref.get()
        if not doc.exists:
            user_ref.set({
                "user_id": user.id,
                "username": user.username if user.username else "N/A",
                "first_name": user.first_name,
                "join_date": firestore.SERVER_TIMESTAMP # অটোমেটিক সার্ভার টাইম
            })
            logger.info(f"👤 New User Saved: {user.id}")
        else:
            logger.info(f"✅ User {user.id} already exists.")
    except Exception as e:
        logger.error(f"❌ Firestore Save Error: {e}")
        # এখানে রেইজ করা ভালো যাতে index.py বুঝতে পারে
        raise e
