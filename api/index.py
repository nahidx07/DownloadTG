import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update, ContentFile
from aiogram.filters import Command
from core.config import BOT_TOKEN, ADMIN_ID
from core.database import save_user, get_all_users
from core.downloader import fetch_media
from core.middlewares import AntiSpamMiddleware

# ১. লগিং সেটআপ (Vercel Logs-এ এরর দেখার জন্য)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ২. বট এবং ডিসপ্যাচার ইনিশিয়ালাইজেশন
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ৩. মিডলওয়্যার যুক্ত করা (Anti-Spam)
dp.message.middleware(AntiSpamMiddleware())

# --- হ্যান্ডলারসমূহ শুরু ---

# ৪. /start কমান্ড হ্যান্ডলার
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        # ইউজার ডাটা ফায়ারবেসে সেভ করা
        await save_user(message.from_user)
        
        welcome_text = (
            f"👋 আসসালামু আলাইকুম, {message.from_user.first_name}!\n\n"
            "আমি একটি **Universal Video Downloader Bot**। 🚀\n\n"
            "**আমি যা যা ডাউনলোড করতে পারি:**\n"
            "✅ TikTok (No Watermark)\n"
            "✅ Facebook Videos & Reels\n"
            "✅ Instagram Reels & Video\n"
            "✅ YouTube Shorts\n\n"
            "📥 শুধু ভিডিওর লিঙ্কটি আমাকে পাঠান, আমি ডাউনলোড করে দিচ্ছি!"
        )
        await message.answer(welcome_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await message.answer("স্বাগতম! আমাকে যে কোনো ভিডিও লিঙ্ক পাঠান।")

# ৫. ভিডিও লিঙ্ক হ্যান্ডলার (TikTok, FB, IG, YT)
@dp.message(F.text.contains("http"))
async def handle_video_links(message: types.Message):
    url = message.text.strip()
    status_msg = await message.answer("⚡ ভিডিওটি প্রসেস করা হচ্ছে, দয়া করে অপেক্ষা করুন...")
    
    try:
        # ডাউনলোডার মডিউল থেকে ডাটা আনা
        media = await fetch_media(url)
        
        if not media or not media.get('url'):
            return await status_msg.edit_text("❌ দুঃখিত! এই লিঙ্কটি সাপোর্ট করছে না অথবা ভিডিওটি খুঁজে পাওয়া যায়নি।")

        # ফাইলের সাইজ চেক করা (যদি ৫০ এমবি এর বেশি হয় তবে ডকুমেন্ট হিসেবে পাঠানো)
        # টেলিগ্রাম বটের মাধ্যমে ২০ এমবি এর বেশি ফাইল পাঠাতে হলে সরাসরি URL ব্যবহার করা ভালো
        file_url = media['url']
        caption = f"🎬 **Title:** {media.get('title', 'Downloaded Video')}\n\n✅ Downloaded by @YourBotUsername"

        try:
            # ভিডিও হিসেবে পাঠানোর চেষ্টা
            await message.reply_video(
                video=file_url, 
                caption=caption, 
                parse_mode="Markdown"
            )
        except Exception:
            # ভিডিও হিসেবে ফেইল করলে ডকুমেন্ট হিসেবে পাঠানো
            await message.reply_document(
                document=file_url, 
                caption=caption, 
                parse_mode="Markdown"
            )
        
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        await status_msg.edit_text(f"⚠️ একটি ত্রুটি ঘটেছে: ভিডিওটি ডাউনলোড করা সম্ভব হয়নি।")

# ৬. এডমিন ব্রডকাস্ট কমান্ড (শুধুমাত্র এডমিনের জন্য)
@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def cmd_broadcast(message: types.Message):
    broadcast_text = message.text.replace("/broadcast", "").strip()
    
    if not broadcast_text:
        return await message.answer("❌ ব্যবহারের নিয়ম: `/broadcast আপনার মেসেজ`")
        
    users = await get_all_users()
    sent_count = 0
    
    status_update = await message.answer(f"📢 {len(users)} জন ইউজারকে মেসেজ পাঠানো শুরু হয়েছে...")
    
    for user_id in users:
        try:
            await bot.send_message(user_id, broadcast_text)
            sent_count += 1
            await asyncio.sleep(0.05) # রেট লিমিট এড়াতে সামান্য বিরতি
        except Exception:
            continue
            
    await status_update.edit_text(f"✅ ব্রডকাস্ট সম্পন্ন হয়েছে!\nসফলভাবে পাঠানো হয়েছে: {sent_count} জনকে।")

# --- Vercel Serverless Function Logic ---

# ৭. এই ফাংশনটি Vercel কল করবে যখন কোনো রিকোয়েস্ট আসবে
async def main(request_data):
    update = Update.model_validate(request_data, context={"bot": bot})
    await dp.feed_update(bot, update)

# এটি Vercel-এর জন্য মূল এন্ট্রি পয়েন্ট
async def handler(request):
    # GET রিকোয়েস্ট (বট চেক করার জন্য)
    if request.method == "GET":
        return {"statusCode": 200, "body": "Bot is running..."}
    
    # POST রিকোয়েস্ট (টেলিগ্রাম থেকে আসা আপডেট)
    if request.method == "POST":
        try:
            body = await request.json()
            await main(body)
            return {"statusCode": 200, "body": "ok"}
        except Exception as e:
            logger.error(f"Webhook Error: {e}")
            return {"statusCode": 500, "body": str(e)}

    return {"statusCode": 405, "body": "Method not allowed"}
