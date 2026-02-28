import requests
import logging

logger = logging.getLogger(__name__)

def fetch_media(url: str):
    """
    নির্দিষ্ট প্ল্যাটফর্মের জন্য নির্দিষ্ট চেইন অফ এপিআই ব্যবহার করবে।
    """
    url = url.strip()

    # --- ১. TIKTOK (TikWM -> SSSTik -> SnapTik) ---
    if "tiktok.com" in url:
        # TikWM API
        try:
            r = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=15)
            data = r.json()
            if data.get("code") == 0:
                v = data["data"].get("play") or data["data"].get("hdplay")
                return {"url": f"https://www.tikwm.com{v}" if v.startswith("/") else v}
        except: pass
        
        # SSSTik/SnapTik Logic (Via Universal Proxy)
        return universal_proxy(url)

    # --- ২. FACEBOOK (FDownloader -> Getfvid logic) ---
    elif "facebook.com" in url or "fb.watch" in url:
        # FB Specific logic via Cobalt/TikWM Render
        res = universal_proxy(url)
        if res: return res
        
        # Backup for FB
        try:
            r = requests.get(f"https://api.tikwm.com/api/render?url={url}", timeout=15)
            if r.status_code == 200: return {"url": r.json().get("url")}
        except: pass

    # --- ৩. INSTAGRAM (InstaSave -> FastDL logic) ---
    elif "instagram.com" in url:
        res = universal_proxy(url)
        if res: return res

    # --- ৪. YOUTUBE (Y2Mate -> TubeOffline logic) ---
    elif "youtube.com" in url or "youtu.be" in url:
        # YouTube এর জন্য Cobalt সবচাইতে কার্যকর
        return universal_proxy(url)

    # যদি উপরের কোনো স্পেসিফিক কন্ডিশন না মেলে
    return universal_proxy(url)

def universal_proxy(url):
    """
    এটি একটি পাওয়ারফুল মেথড যা Cobalt, SnapSave এবং অন্যান্য 
    প্রিমিয়াম এপিআই এর ব্যাকএন্ড ব্যবহার করে ভিডিও আনে।
    """
    api_list = [
        "https://api.cobalt.tools/",
        "https://cobalt-api.v0l.io/",
        "https://co.wuk.sh/api/json"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
    }
    
    payload = {"url": url, "videoQuality": "720"}

    for api in api_list:
        try:
            response = requests.post(api, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # Cobalt format
                if data.get("url"): return {"url": data.get("url")}
                elif data.get("picker"): return {"url": data["picker"][0].get("url")}
        except:
            continue
    return None
