import os
import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update
from aiogram.filters import Command

# লোকাল মডিউল ইমপোর্ট
try:
    from core.config import BOT_TOKEN, ADMIN_ID
    from core.database import save_user, get_all_users
    from core.downloader import fetch_media
    from core.middlewares import AntiSpamMiddleware
except ImportError as e:
    print(f"Import Error: {e}")

# লগিং কনফিগারেশন
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# বট ও ডিসপ্যাচার ইনিশিয়ালাইজেশন
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# মিডলওয়্যার
try:
    dp.message.middleware(AntiSpamMiddleware())
except:
    pass

# --- বটের মূল হ্যান্ডলারসমূহ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        # ফায়ারবেসে সেভ করার চেষ্টা (এরর হলেও বট যেন রিপ্লাই দেয়)
        try:
            await save_user(message.from_user)
        except Exception as db_err:
            logger.error(f"Database Error: {db_err}")
            
        await message.answer(
            f"👋 আসসালামু আলাইকুম, {message.from_user.first_name}!\n\n"
            "আমি একটি **All-in-One Downloader Bot**।\n"
            "যেকোনো ভিডিওর লিঙ্ক পাঠান, আমি সেটি ডাউনলোড করে দিচ্ছি।",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Start Error: {e}")

@dp.message(F.text.contains("http"))
async def handle_download(message: types.Message):
    status = await message.answer("⚡ ভিডিওটি প্রসেস করা হচ্ছে...")
    try:
        media = await fetch_media(message.text.strip())
        if not media or not media.get('url'):
            return await status.edit_text("❌ দুঃখিত! এই লিঙ্ক থেকে ভিডিও পাওয়া যায়নি।")

        # ভিডিও পাঠানোর চেষ্টা
        try:
            await message.reply_video(video=media['url'], caption="✅ ডাউনলোড সম্পন্ন!")
        except:
            await message.reply_document(document=media['url'], caption="✅ ফাইল হিসেবে পাঠানো হলো।")
        
        await status.delete()
    except Exception as e:
        logger.error(f"Download Error: {e}")
        await status.edit_text("⚠️ ভিডিওটি পাঠাতে সমস্যা হয়েছে।")

# --- Vercel এর জন্য মূল হ্যান্ডলার ক্লাস ---

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """টেলিগ্রাম থেকে আসা রিকোয়েস্ট হ্যান্ডেল করে"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update_data = json.loads(post_data.decode('utf-8'))
            
            # একটি নতুন ইভেন্ট লুপ তৈরি করা (Vercel/Serverless এর জন্য জরুরি)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # আপডেট প্রসেস করা
            update = Update.model_validate(update_data, context={"bot": bot})
            loop.run_until_complete(dp.feed_update(bot, update))
            loop.close()

            # রেসপন্স পাঠানো
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            logger.error(f"Webhook Execution Error: {e}")
            # ৫৩০০ এরর না পাঠিয়ে ২০০ পাঠানো ভালো যাতে টেলিগ্রাম বারবার রিকোয়েস্ট না পাঠায়
            self.send_response(200) 
            self.end_headers()

    def do_GET(self):
        """সার্ভার চেক করার জন্য"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        response = "<h1>Bot is Running!</h1><p>Send a message to your bot on Telegram.</p>"
        self.wfile.write(response.encode('utf-8'))
