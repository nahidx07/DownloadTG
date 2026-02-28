import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str):
    # আমরা Cobalt এর একটি পাবলিক ইনস্ট্যান্স ব্যবহার করছি যা সব প্ল্যাটফর্ম সাপোর্ট করে
    # এটি FB, IG, YouTube, Twitter সবকিছুর জন্য কাজ করে
    api_url = "https://cobalt-api.v0l.io/" 
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # এপিআই পেলোড (ভিডিও সেটিংস)
    payload = {
        "url": url,
        "videoQuality": "720",
        "audioFormat": "mp3",
        "filenameStyle": "basic",
        "downloadMode": "video"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # POST রিকোয়েস্ট পাঠানো
            response = await client.post(api_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"API returned status {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            # Cobalt API এর রেসপন্স হ্যান্ডেল করা
            # এটি সরাসরি ভিডিও লিঙ্ক (url) অথবা মাল্টিপল অপশন (picker) দেয়
            if data.get("status") in ["stream", "redirect", "picker"]:
                video_url = data.get("url")
                
                # যদি ইউটিউব বা ফেসবুকের ক্ষেত্রে ভিডিও লিঙ্ক সরাসরি না পাওয়া যায়
                if not video_url and data.get("picker"):
                    video_url = data["picker"][0].get("url")

                if video_url:
                    return {
                        "url": video_url,
                        "title": "Downloaded Video",
                    }
            elif data.get("status") == "error":
                logger.warning(f"Cobalt Error: {data.get('text')}")
                
    except Exception as e:
        logger.error(f"Downloader Error: {e}")
    
    return None
