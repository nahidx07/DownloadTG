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

# বাটন মেনু তৈরি
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Facebook 🔵"), KeyboardButton(text="Instagram 📷")],
        [KeyboardButton(text="TikTok 🎵"), KeyboardButton(text="YouTube 🔴")],
        [KeyboardButton(text="Trend/Other 🌐")]
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
            f"👋 আসসালামু আলাইকুম {message.from_user.first_name}!\nনিচের বাটন থেকে প্ল্যাটফর্ম সিলেক্ট করুন:",
            reply_markup=main_menu
        )

    # বাটন ক্লিকের রেসপন্স
    @dp.message(F.text.in_(["Facebook 🔵", "Instagram 📷", "TikTok 🎵", "YouTube 🔴", "Trend/Other 🌐"]))
    async def platform_selected(message: types.Message):
        platform = message.text.split()[0]
        await message.answer(f"📥 আপনার {platform} ভিডিও লিঙ্কটি এখানে পাঠান:")

    # লিঙ্ক হ্যান্ডলিং
    @dp.message(F.text.contains("http"))
    async def handle_links(message: types.Message):
        status = await message.answer("⚡ ভিডিওটি প্রসেস করা হচ্ছে, দয়া করে অপেক্ষা করুন...")
        try:
            # downloader.py থেকে মিডিয়া আনা
            media = await fetch_media(message.text.strip())
            
            if media and media.get('url'):
                try:
                    await message.reply_video(video=media['url'], caption="✅ ডাউনলোড সম্পন্ন!")
                except:
                    # বড় ফাইল হলে ডকুমেন্ট হিসেবে পাঠানো
                    await message.reply_document(document=media['url'], caption="✅ বড় ফাইল হিসেবে পাঠানো হলো।")
                await status.delete()
            else:
                await status.edit_text("❌ দুঃখিত! এই লিঙ্ক থেকে ভিডিও পাওয়া যায়নি। পাবলিক লিঙ্ক দিয়ে আবার চেষ্টা করুন।")
        except Exception as e:
            logger.error(f"Error: {e}")
            await status.edit_text("⚠️ কারিগরি ত্রুটি! লিঙ্কে সমস্যা হতে পারে।")

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
        except Exception as e:
            logger.error(f"Error: {e}")
            self.send_response(200)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.wfile.write("Bot is Live with Buttons! 🚀".encode())
