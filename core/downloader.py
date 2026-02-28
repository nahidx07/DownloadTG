import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str):
    # ১. যদি লিঙ্কটি টিকটকের হয়, তবে TikWM (আগের সফল পদ্ধতি) ব্যবহার করবে
    if "tiktok.com" in url:
        tikwm_url = "https://www.tikwm.com/api/"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(tikwm_url, data={"url": url})
                data = resp.json()
                if data.get("code") == 0:
                    video = data["data"].get("play") or data["data"].get("hdplay")
                    return {"url": f"https://www.tikwm.com{video}" if video.startswith("/") else video}
        except Exception as e:
            logger.error(f"TikTok Specific Error: {e}")

    # ২. ফেসবুক, ইন্সটাগ্রাম বা ইউটিউবের জন্য Cobalt API ব্যবহার করবে
    # আমি এখানে ৩টি ভিন্ন ভিন্ন এপিআই লিঙ্ক দিচ্ছি, একটি না হলে অন্যটি কাজ করবে
    api_list = [
        "https://api.cobalt.tools/",
        "https://cobalt-api.v0l.io/",
        "https://cobalt.sh/"
    ]
    
    payload = {
        "url": url,
        "videoQuality": "720",
        "filenameStyle": "basic"
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    for api in api_list:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.post(api, json=payload, headers=headers)
                if response.status_code == 200:
                    res_data = response.json()
                    status = res_data.get("status")
                    
                    if status in ["stream", "redirect", "video"]:
                        return {"url": res_data.get("url")}
                    elif status == "picker":
                        return {"url": res_data["picker"][0].get("url")}
        except:
            continue # একটি এপিআই কাজ না করলে পরেরটি ট্রাই করবে
            
    return None
