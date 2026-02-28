import requests
import logging
import time

logger = logging.getLogger(__name__)

def fetch_media(url: str):
    """
    Vercel-এ Errno 16 এড়াতে আমরা requests লাইব্রেরি ব্যবহার করছি যা কম রিসোর্স খরচ করে।
    """
    
    # ১. TikTok এর জন্য (TikWM)
    if "tiktok.com" in url:
        try:
            r = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("code") == 0:
                    v = data["data"].get("play") or data["data"].get("hdplay")
                    return {"url": f"https://www.tikwm.com{v}" if v.startswith("/") else v}
        except Exception as e:
            logger.error(f"TikTok Error: {e}")

    # ২. Facebook, Instagram, YouTube এর জন্য (Cobalt API)
    # আমরা সরাসরি ১টি স্টেবল সার্ভার ব্যবহার করছি লুপ এড়াতে
    api_url = "https://cobalt-api.v0l.io/"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
    }
    
    payload = {
        "url": url,
        "videoQuality": "720"
    }

    try:
        # Resource busy এরর এড়াতে requests ব্যবহার করা হলো
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        
        if response.status_code == 200:
            res_data = response.json()
            # সরাসরি ইউআরএল চেক
            if res_data.get("url"):
                return {"url": res_data.get("url")}
            # যদি পিকার থাকে (YouTube/FB এর জন্য)
            elif res_data.get("picker"):
                return {"url": res_data["picker"][0].get("url")}
                
        # ব্যাকআপ চেষ্টা (যদি প্রথমটি ফেইল করে)
        else:
            logger.info("Trying backup renderer...")
            alt_url = f"https://api.tikwm.com/api/render?url={url}"
            alt_r = requests.get(alt_url, timeout=15)
            if alt_r.status_code == 200:
                return {"url": alt_r.json().get("url")}

    except Exception as e:
        logger.error(f"Universal Downloader Error: {e}")
            
    return None
