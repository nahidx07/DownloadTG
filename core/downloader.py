import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str):
    # টিকটকের জন্য (আপনার যেটা কাজ করছিল)
    if "tiktok.com" in url:
        tikwm_url = "https://www.tikwm.com/api/"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(tikwm_url, data={"url": url})
                data = resp.json()
                if data.get("code") == 0:
                    video = data["data"].get("play") or data["data"].get("hdplay")
                    return {"url": f"https://www.tikwm.com{video}" if video.startswith("/") else video}
        except: pass

    # ফেসবুক, ইন্সটাগ্রাম ও ইউটিউবের জন্য (নতুন ৩টি আলাদা এপিআই ব্যাকআপ)
    apis = [
        "https://api.cobalt.tools/",
        "https://cobalt-api.v0l.io/",
        "https://api.tikwm.com/api/render" # ব্যাকআপ
    ]
    
    payload = {"url": url, "videoQuality": "720", "filenameStyle": "basic"}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    for api in apis:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # যদি ফেসবুক বা ইউটিউব হয়
                response = await client.post(api, json=payload, headers=headers)
                if response.status_code == 200:
                    res = response.json()
                    if res.get("status") in ["stream", "redirect", "video"]:
                        return {"url": res.get("url")}
                    elif res.get("status") == "picker":
                        return {"url": res["picker"][0].get("url")}
        except:
            continue
            
    return None
