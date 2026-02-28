import os
import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# লজিক্যাল মডিউল ইম্পোর্ট
from core.config import BOT_TOKEN
from core.database import save_user
from core.downloader import fetch_media # এটি এখন সিঙ্ক্রোনাস ফাংশন

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# বাটন মেনু তৈরি
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Facebook 🔵"), KeyboardButton(text="Instagram 📷")],
        [KeyboardButton(text="TikTok 🎵"), KeyboardButton(text="YouTube 🔴")],
        [KeyboardButton(text="Others 🌐")]
    ],
    resize_keyboard=True
)

# --- মূল প্রসেসিং ফাংশন ---
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
    async def ask_for_link(message: types.Message):
        platform = message.text.split()[0]
        await message.answer(f"📥 আপনার {platform} ভিডিও লিঙ্কটি এখানে পেস্ট করুন:")

    @dp.message(F.text.contains("http"))
    async def handle_links(message: types.Message):
        status = await message.answer("⏳ ভিডিওটি প্রসেস করা হচ্ছে, দয়া করে অপেক্ষা করুন...")
        
        try:
            # গুরুত্বপূর্ণ পরিবর্তন: fetch_media এখন আর await দরকার নেই
            # কারণ আমরা রিসোর্স এরর এড়াতে এটাকে sync করেছি
            res = fetch_media(message.text.strip())
            
            if res and res.get('url'):
                try:
                    # ভিডিও হিসেবে পাঠানোর চেষ্টা
                    await message.reply_video(video=res['url'], caption="✅ ডাউনলোড সম্পন্ন!")
                except Exception as video_err:
                    logger.warning(f"Video send failed: {video_err}")
                    # ভিডিও ফেইল করলে ফাইল (Document) হিসেবে পাঠানো (বড় ফাইলের জন্য)
                    await message.reply_document(document=res['url'], caption="✅ ফাইল হিসেবে পাঠানো হলো।")
                
                await status.delete()
            else:
                await status.edit_text("❌ দুঃখিত! এই লিঙ্ক থেকে ভিডিও পাওয়া যায়নি। দয়া করে পাবলিক লিঙ্ক ব্যবহার করুন।")
        
        except Exception as e:
            logger.error(f"Processing Error: {e}")
            await status.edit_text("⚠️ একটি কারিগরি ত্রুটি ঘটেছে। আবার চেষ্টা করুন।")

    # আপডেট হ্যান্ডেল করা
    try:
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    finally:
        # সেশন বন্ধ করা (মেমোরি ও রিসোর্স সেভ করার জন্য)
        await bot.session.close()

# --- Vercel Serverless Handler ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update_dict = json.loads(post_data.decode('utf-8'))
            
            # নতুন ইভেন্ট লুপে রান করা
            asyncio.run(main_process(update_dict))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            logger.error(f"Critical Webhook Error: {e}")
            self.send_response(200) # টেলিগ্রামকে সবসময় ২০০ দিতে হয়
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot is Finalized and Live! 🚀".encode('utf-8'))
