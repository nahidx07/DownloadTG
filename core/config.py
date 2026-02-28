import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# সেফলি ফায়ারবেস ক্রেড লোড করা
firebase_raw = os.getenv("FIREBASE_SERVICE_ACCOUNT")
try:
    FIREBASE_CREDS = json.loads(firebase_raw) if firebase_raw else {}
except Exception as e:
    print(f"Firebase JSON Error: {e}")
    FIREBASE_CREDS = {}
  
