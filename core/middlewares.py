from aiogram import BaseMiddleware
from aiogram.types import Message
import time

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, limit=5):
        self.last_user_time = {}
        self.limit = limit
        super().__init__()

    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        current_time = time.time()
        
        if user_id in self.last_user_time:
            if current_time - self.last_user_time[user_id] < self.limit:
                return await event.answer("⚠️ দয়া করে ৫ সেকেন্ড অপেক্ষা করুন!")
        
        self.last_user_time[user_id] = current_time
        return await handler(event, data)
