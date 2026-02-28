import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str, retries=3):
    # আমরা TikWM এর গ্লোবাল এপিআই ব্যবহার করছি
    api_url = "https://www.tikwm.com/api/"
    
    # ইউজার এজেন্ট (এটি না থাকলে অনেক সময় এপিআই ব্লক করে দেয়)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    for i in range(retries):
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
                # টিকটকের জন্য সরাসরি এপিআই কল
                response = await client.post(api_url, data={"url": url})
                
                # যদি এপিআই থেকে রেসপন্স না আসে
                if response.status_code != 200:
                    logger.error(f"API returned status {response.status_code}")
                    continue

                data = response.json()
                
                if data.get("code") == 0:
                    res = data["data"]
                    # ভিডিও লিঙ্ক খুঁজে বের করা
                    video_url = res.get("play") or res.get("hdplay") or res.get("wmplay")
                    
                    if video_url:
                        # যদি লিঙ্কটি পূর্ণাঙ্গ না হয় তবে ডোমেইন যোগ করা
                        if video_url.startswith("/"):
                            video_url = f"https://www.tikwm.com{video_url}"
                            
                        return {
                            "url": video_url,
                            "title": res.get("title", "Video"),
                            "size": res.get("size", 0)
                        }
                else:
                    logger.warning(f"API Error Message: {data.get('msg')}")

        except Exception as e:
            logger.error(f"Retry {i+1} failed: {e}")
            if i == retries - 1:
                return None
            await asyncio.sleep(2) # ২ সেকেন্ড অপেক্ষা করে আবার ট্রাই করবে
            
    return None
