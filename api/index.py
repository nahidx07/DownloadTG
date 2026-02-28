import os
import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update
from aiogram.filters import Command

# আপনার লোকাল মডিউলগুলো ইমপোর্ট করা
from core.config import BOT_TOKEN, ADMIN_ID
from core.database import save_user, get_all_users
from core.downloader import fetch_media
from core.middlewares import AntiSpamMiddleware

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# বট ও ডিসপ্যাচার সেটআপ
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# মিডলওয়্যার (স্প্যাম প্রোটেকশন)
dp.message.middleware(AntiSpamMiddleware())

# --- টেলিগ্রাম হ্যান্ডলারসমূহ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        await save_user(message.from_user)
        welcome_text = (
            f"👋 আসসালামু আলাইকুম, {message.from_user.first_name}!\n\n"
            "আমি একটি **Universal Video Downloader Bot**।\n"
            "যেকোনো ভিডিওর লিঙ্ক পাঠান, আমি সেটি ডাউনলোড করে দিচ্ছি।"
        )
        await message.answer(welcome_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await message.answer("স্বাগতম!")

@dp.message(F.text.contains("http"))
async def handle_links(message: types.Message):
    status_msg = await message.answer("⏳ প্রসেসিং হচ্ছে...")
    try:
        media = await fetch_media(message.text.strip())
        if not media or not media.get('url'):
            return await status_msg.edit_text("❌ ভিডিওটি পাওয়া যায়নি বা লিঙ্কটি ভুল।")

        file_url = media['url']
        caption = f"✅ Success!\n\n🎬 {media.get('title', 'Video')}"

        try:
            await message.reply_video(video=file_url, caption=caption)
        except:
            await message.reply_document(document=file_url, caption=caption)
        
        await status_msg.delete()
    except Exception as e:
        logger.error(f"Download Error: {e}")
        await status_msg.edit_text("⚠️ ভিডিওটি ডাউনলোড করতে সমস্যা হয়েছে।")

@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def cmd_broadcast(message: types.Message):
    text = message.text.replace("/broadcast", "").strip()
    if not text: return await message.answer("মেসেজ লিখুন।")
    
    users = await get_all_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            count += 1
        except: continue
    await message.answer(f"✅ {count} জনকে পাঠানো হয়েছে।")

# --- Vercel Serverless Handler (The Fix) ---

async def process_event(event):
    """টেলিগ্রাম আপডেট প্রসেস করার মূল ফাংশন"""
    try:
        update = Update.model_validate(event, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Process Event Error: {e}")

class handler(BaseHTTPRequestHandler):
    """Vercel এই ক্লাসটিকেই কল করবে"""
    
    def do_POST(self):
        """টেলিগ্রাম থেকে আসা POST রিকোয়েস্ট হ্যান্ডেল করে"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            update_dict = json.loads(post_data.decode('utf-8'))

            # Async ইভেন্ট লুপে রান করা
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_event(update_dict))
            loop.close()

            # টেলিগ্রামকে ২০০ ওকে রেসপন্স পাঠানো
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        except Exception as e:
            logger.error(f"Handler POST Error: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        """ব্রাউজারে চেক করার জন্য GET রিকোয়েস্ট"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("বটটি সফলভাবে চালু হয়েছে! 🚀".encode('utf-8'))
