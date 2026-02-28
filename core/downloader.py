import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str):
    # স্তর ১: টিকটকের জন্য স্পেশাল এপিআই
    if "tiktok.com" in url:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post("https://www.tikwm.com/api/", data={"url": url})
                data = r.json()
                if data.get("code") == 0:
                    v = data["data"].get("play") or data["data"].get("hdplay")
                    return {"url": f"https://www.tikwm.com{v}" if v.startswith("/") else v}
        except: pass

    # স্তর ২: ফেসবুক, ইন্সটাগ্রাম ও ইউটিউবের জন্য মাস্টার এপিআই
    # আমরা এখানে ৩টি ভিন্ন ভিন্ন ইঞ্জিন ট্রাই করবো
    engines = [
        "https://api.cobalt.tools/", 
        "https://cobalt-api.v0l.io/",
        "https://co.wuk.sh/api/json"
    ]
    
    payload = {"url": url, "videoQuality": "720", "filenameStyle": "basic"}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    for engine in engines:
        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                response = await client.post(engine, json=payload, headers=headers)
                if response.status_code == 200:
                    res_data = response.json()
                    # যদি সরাসরি ইউআরএল থাকে
                    if res_data.get("url"):
                        return {"url": res_data.get("url")}
                    # যদি পিকার বা লিস্ট থাকে
                    elif res_data.get("picker"):
                        return {"url": res_data["picker"][0].get("url")}
        except Exception as e:
            logger.error(f"Engine {engine} failed: {e}")
            continue
            
    return None
