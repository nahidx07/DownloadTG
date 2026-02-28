import os
import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update
from aiogram.filters import Command

# লজিক্যাল মডিউল ইম্পোর্ট
from core.config import BOT_TOKEN, ADMIN_ID
from core.database import save_user, get_all_users
from core.downloader import fetch_media
from core.middlewares import AntiSpamMiddleware

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ১. বট ও ডিসপ্যাচার গ্লোবালি ইনিশিয়ালাইজ করা
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AntiSpamMiddleware())

# --- টেলিগ্রাম হ্যান্ডলারসমূহ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await save_user(message.from_user)
    await message.answer(f"👋 আসসালামু আলাইকুম {message.from_user.first_name}!\nযেকোনো সোশ্যাল মিডিয়া লিঙ্ক পাঠান, আমি ভিডিও ডাউনলোড করে দিচ্ছি।")

@dp.message(F.text.contains("http"))
async def handle_video(message: types.Message):
    msg = await message.answer("⏳ প্রসেসিং হচ্ছে, দয়া করে অপেক্ষা করুন...")
    try:
        media = await fetch_media(message.text.strip())
        if media and media.get('url'):
            # ভিডিও পাঠানোর চেষ্টা, না পারলে ডকুমেন্ট হিসেবে পাঠানো
            try:
                await message.reply_video(video=media['url'], caption="✅ ডাউনলোড সম্পন্ন!")
            except:
                await message.reply_document(document=media['url'], caption="✅ ফাইল হিসেবে পাঠানো হলো।")
            await msg.delete()
        else:
            await msg.edit_text("❌ দুঃখিত! এই লিঙ্ক থেকে ভিডিও পাওয়া যায়নি।")
    except Exception as e:
        logger.error(f"Downloader Error: {e}")
        await msg.edit_text("⚠️ একটি কারিগরি ত্রুটি ঘটেছে। আবার চেষ্টা করুন।")

# --- মূল ফাংশন যা আপডেট প্রসেস করবে (Async) ---

async def main_process(update_data):
    # প্রতিটি রিকোয়েস্টের জন্য এই ফাংশনটি নতুনভাবে এক্সিকিউট হবে
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)

# --- Vercel Handler Class ---

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """টেলিগ্রাম থেকে আসা POST রিকোয়েস্ট হ্যান্ডেল করে"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update_dict = json.loads(post_data.decode('utf-8'))
            
            # সমাধান: asyncio.run() ব্যবহার করা
            # এটি একটি ফ্রেশ ইভেন্ট লুপ তৈরি করে, কাজ শেষ করে এবং লুপটি প্রপারলি বন্ধ করে দেয়।
            asyncio.run(main_process(update_dict))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            logger.error(f"Critical Webhook Error: {e}")
            # টেলিগ্রামকে সব সময় ২০০ ওকে পাঠানো ভালো যাতে পেন্ডিং আপডেট জমে না থাকে
            self.send_response(200) 
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

    def do_GET(self):
        """সার্ভার চেক করার জন্য GET রিকোয়েস্ট"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot is Live and Running! 🚀".encode('utf-8'))
