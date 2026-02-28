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

# --- মূল ফাংশন যা প্রতিটি রিকোয়েস্টে নতুনভাবে রান হবে ---

async def main_process(update_data):
    # ১. এখানে নতুনভাবে Bot এবং Dispatcher তৈরি করা হচ্ছে (লুপ এরর এড়াতে)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # ২. মিডলওয়্যার এবং হ্যান্ডলার রেজিস্টার করা
    dp.message.middleware(AntiSpamMiddleware())

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await save_user(message.from_user)
        await message.answer(f"👋 স্বাগতম {message.from_user.first_name}!\nলিঙ্ক পাঠান, আমি ডাউনলোড করছি।")

    @dp.message(F.text.contains("http"))
    async def handle_video(message: types.Message):
        status = await message.answer("⏳ প্রসেসিং...")
        try:
            media = await fetch_media(message.text.strip())
            if media and media.get('url'):
                try:
                    await message.reply_video(video=media['url'], caption="✅ সম্পন্ন!")
                except:
                    await message.reply_document(document=media['url'], caption="✅ ফাইল হিসেবে পাঠানো হলো।")
                await status.delete()
            else:
                await status.edit_text("❌ ভিডিও পাওয়া যায়নি।")
        except Exception as e:
            logger.error(f"Downloader Error: {e}")
            await status.edit_text("⚠️ ত্রুটি ঘটেছে।")

    # ৩. আপডেট প্রসেস করা
    try:
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    finally:
        # সেশন বন্ধ করা (মেমোরি লিক এড়াতে)
        await bot.session.close()

# --- Vercel Handler Class ---

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update_dict = json.loads(post_data.decode('utf-8'))
            
            # নতুন ফ্রেশ ইভেন্ট লুপে প্রসেস করা
            asyncio.run(main_process(update_dict))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            logger.error(f"FINAL Webhook Error: {e}")
            self.send_response(200)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot is Finalized and Live! 🚀".encode('utf-8'))
