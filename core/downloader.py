import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str):
    # --- ১. TikTok স্পেসিফিক চেইন (TikWM -> SSSTik -> Cobalt) ---
    if "tiktok.com" in url:
        # TikWM (Best for TikTok)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post("https://www.tikwm.com/api/", data={"url": url})
                data = r.json()
                if data.get("code") == 0:
                    v = data["data"].get("play") or data["data"].get("hdplay")
                    return {"url": f"https://www.tikwm.com{v}" if v.startswith("/") else v}
        except: pass

    # --- ২. Universal চেইন (Facebook, Instagram, YouTube এর জন্য) ---
    # এখানে আমরা Cobalt, SnapSave, এবং Rapid-সার্ভিসগুলোর মাল্টিপল ব্যাকআপ রাখছি
    
    engines = [
        # ইঞ্জিন ১: Cobalt (YouTube, FB, IG এর জন্য সবচাইতে শক্তিশালী)
        {"url": "https://api.cobalt.tools/", "type": "json"},
        {"url": "https://cobalt-api.v0l.io/", "type": "json"},
        
        # ইঞ্জিন ২: Loapi / Alternative (SnapSave logic)
        {"url": "https://api.tikwm.com/api/render", "type": "json"},
        
        # ইঞ্জিন ৩: অল্টারনেটিভ প্রক্সি সার্ভিস
        {"url": "https://co.wuk.sh/api/json", "type": "json"}
    ]

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    payload = {
        "url": url,
        "videoQuality": "720",
        "filenameStyle": "basic",
        "downloadMode": "video"
    }

    for engine in engines:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.post(engine["url"], json=payload, headers=headers)
                
                if response.status_code == 200:
                    res_data = response.json()
                    
                    # Cobalt Format
                    if res_data.get("status") in ["stream", "redirect", "video"]:
                        return {"url": res_data.get("url")}
                    elif res_data.get("status") == "picker":
                        return {"url": res_data["picker"][0].get("url")}
                    
                    # Other API Format
                    elif res_data.get("url"):
                        return {"url": res_data.get("url")}
                        
        except Exception as e:
            logger.error(f"Engine {engine['url']} failed: {e}")
            continue # একটি কাজ না করলে পরেরটিতে চলে যাবে

    # --- ৩. যদি কোনোটিই কাজ না করে (Final Search) ---
    return None
