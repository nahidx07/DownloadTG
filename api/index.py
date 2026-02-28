import os
import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from core.config import BOT_TOKEN
from core.database import save_user
from core.downloader import fetch_media

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# বাটন মেনু
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Facebook 🔵"), KeyboardButton(text="Instagram 📷")],
        [KeyboardButton(text="TikTok 🎵"), KeyboardButton(text="YouTube 🔴")],
        [KeyboardButton(text="Others 🌐")]
    ],
    resize_keyboard=True
)

async def main_process(update_data):
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await save_user(message.from_user)
        await message.answer(
            f"👋 আসসালামু আলাইকুম {message.from_user.first_name}!\nনিচের বাটন থেকে প্ল্যাটফর্ম সিলেক্ট করুন অথবা সরাসরি লিঙ্ক পাঠান:",
            reply_markup=main_menu
        )

    @dp.message(F.text.in_(["Facebook 🔵", "Instagram 📷", "TikTok 🎵", "YouTube 🔴", "Others 🌐"]))
    async def ask_link(message: types.Message):
        platform = message.text.split()[0]
        await message.answer(f"📥 আপনার {platform} ভিডিও লিঙ্কটি দিন:")

    @dp.message(F.text.contains("http"))
    async def handle_download(message: types.Message):
        status = await message.answer("⚡ ভিডিওটি প্রসেস করা হচ্ছে, কিছুক্ষণ অপেক্ষা করুন...")
        try:
            res = await fetch_media(message.text.strip())
            if res and res.get('url'):
                try:
                    # ভিডিও হিসেবে পাঠানোর চেষ্টা
                    await message.reply_video(video=res['url'], caption="✅ আপনার ভিডিও প্রস্তুত!")
                except:
                    # ভিডিও ফেইল করলে ফাইল হিসেবে পাঠানো
                    await message.reply_document(document=res['url'], caption="✅ ফাইল হিসেবে পাঠানো হলো।")
                await status.delete()
            else:
                await status.edit_text("❌ দুঃখিত! এই লিঙ্ক থেকে ভিডিও পাওয়া যায়নি। দয়া করে পাবলিক লিঙ্ক ব্যবহার করুন।")
        except Exception as e:
            logger.error(f"Error: {e}")
            await status.edit_text("⚠️ কারিগরি ত্রুটি! আবার চেষ্টা করুন।")

    try:
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    finally:
        await bot.session.close()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            update_dict = json.loads(post_data.decode('utf-8'))
            asyncio.run(main_process(update_dict))
            self.send_response(200)
            self.end_headers()
        except:
            self.send_response(200)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Bot is Finalized! 🚀".encode())
