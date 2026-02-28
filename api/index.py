from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update
from core.config import BOT_TOKEN, ADMIN_ID
from core.database import save_user, get_all_users
from core.downloader import fetch_media
from core.middlewares import AntiSpamMiddleware
import asyncio

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AntiSpamMiddleware())

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await save_user(message.from_user)
    await message.answer("👋 স্বাগতম! আমাকে FB, IG, TikTok বা YouTube লিঙ্ক পাঠান।")

@dp.message(F.text.startswith("http"))
async def handle_links(message: types.Message):
    status_msg = await message.answer("⏳ প্রসেসিং হচ্ছে...")
    try:
        media = await fetch_media(message.text)
        if not media or not media['url']:
            return await status_msg.edit_text("❌ ভিডিও লিঙ্ক পাওয়া যায়নি।")

        # ৫০এমবি এর বেশি হলে ডকুমেন্ট হিসেবে পাঠানো
        if media['size'] > 48000000:
            await message.reply_document(media['url'], caption=media['title'])
        else:
            await message.reply_video(media['url'], caption=media['title'])
        
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"⚠️ ত্রুটি: {str(e)}")

@dp.message(F.text.startswith("/broadcast"), F.from_user.id == ADMIN_ID)
async def cmd_broadcast(message: types.Message):
    text = message.text.replace("/broadcast ", "")
    users = await get_all_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            count += 1
        except: continue
    await message.answer(f"✅ {count} জন ইউজারকে মেসেজ পাঠানো হয়েছে।")

# Vercel Handler
async def handler(request):
    if request.method == "POST":
        body = await request.json()
        update = Update.model_validate(body, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"statusCode": 200}
    return {"statusCode": 405}
