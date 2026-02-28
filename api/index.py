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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# বট ও ডিসপ্যাচার গ্লোবালি ইনিশিয়ালাইজ করা
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AntiSpamMiddleware())

# --- টেলিগ্রাম হ্যান্ডলারসমূহ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await save_user(message.from_user)
    await message.answer(f"👋 আসসালামু আলাইকুম {message.from_user.first_name}!\nলিঙ্ক পাঠান, আমি ভিডিও নামিয়ে দিচ্ছি।")

@dp.message(F.text.contains("http"))
async def handle_video(message: types.Message):
    msg = await message.answer("⏳ প্রসেসিং...")
    try:
        media = await fetch_media(message.text.strip())
        if media and media.get('url'):
            await message.reply_video(video=media['url'], caption="✅ সম্পন্ন!")
            await msg.delete()
        else:
            await msg.edit_text("❌ ভিডিও পাওয়া যায়নি।")
    except Exception as e:
        logger.error(f"Downloader Error: {e}")
        await msg.edit_text("⚠️ ত্রুটি ঘটেছে।")

# --- মূল ফাংশন যা আপডেট প্রসেস করবে ---

async def main_process(update_data):
    # এই ফাংশনটি প্রতিটি রিকোয়েস্টের জন্য আলাদাভাবে রান হবে
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)

# --- Vercel Handler Class ---

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update_dict = json.loads(post_data.decode('utf-8'))
            
            # সমাধান: asyncio.run() ব্যবহার করা
            # এটি একটি ফ্রেশ লুপ তৈরি করে, কাজ শেষ করে এবং লুপটি বন্ধ করে দেয়।
            asyncio.run(main_process(update_dict))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            logger.error(f"Webhook Execution Error: {e}")
            # টেলিগ্রামকে সব সময় ২০০ পাঠাতে হয় যাতে সে রিট্রাই না করে
            self.send_response(200) 
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot is Live! 🚀".encode('utf-8'))
