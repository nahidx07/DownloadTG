import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str):
    # ১. যদি টিকটক হয় (এটি আপনার অলরেডি কাজ করছে)
    if "tiktok.com" in url:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post("https://www.tikwm.com/api/", data={"url": url})
                data = r.json()
                if data.get("code") == 0:
                    v = data["data"].get("play") or data["data"].get("hdplay")
                    return {"url": f"https://www.tikwm.com{v}" if v.startswith("/") else v}
        except: pass

    # ২. ফেসবুক, ইউটিউব ও ইন্সটাগ্রামের জন্য নতুন এবং সহজ মেথড
    # আমরা এখানে 'cobalt' এর বদলে সরাসরি 'AIO Downloader' প্রক্সি ব্যবহার করছি
    
    # এরর এড়াতে আমরা লুপ না চালিয়ে সরাসরি শক্তিশালী একটি এপিআই আগে ট্রাই করবো
    target_api = "https://cobalt-api.v0l.io/" # ব্যাকআপ এপিআই
    
    # 400 Bad Request এড়াতে নতুন পে-লোড ফরম্যাট
    payload = {
        "url": url,
        "videoQuality": "720",
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # প্রথম চেষ্টা
            response = await client.post(target_api, json=payload, headers=headers)
            
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("url"):
                    return {"url": res_data.get("url")}
                elif res_data.get("picker"):
                    return {"url": res_data["picker"][0].get("url")}
            
            # যদি প্রথমটি ফেইল করে, তবে দ্রুত অন্য একটি প্রক্সি ট্রাই করা (TikWM Proxy)
            elif response.status_code != 200:
                logger.info("Switching to Backup Proxy...")
                # এই এপিআইটি ফেসবুক ও ইন্সটাগ্রামের জন্য খুব ভালো কাজ করে
                alt_api = "https://api.tikwm.com/api/render"
                alt_response = await client.get(f"{alt_api}?url={url}")
                if alt_response.status_code == 200:
                    alt_data = alt_response.json()
                    if alt_data.get("url"):
                        return {"url": alt_data.get("url")}

    except Exception as e:
        logger.error(f"Downloader Error: {e}")
            
    return None
