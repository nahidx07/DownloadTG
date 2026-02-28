import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
# Firebase credentials JSON string থেকে ডিকশনারিতে রূপান্তর
FIREBASE_CREDS = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))
