import httpx
import asyncio

async def fetch_media(url: str, retries=2):
    # একাধিক প্ল্যাটফর্ম সাপোর্ট করে এমন একটি এপিআই (যেমন: TikWM বা Cobalt)
    api_url = "https://www.tikwm.com/api/v2/unidown" 
    
    for i in range(retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, data={"url": url})
                data = response.json()
                
                if data.get("code") == 0:
                    res = data["data"]
                    return {
                        "url": res.get("video") or res.get("play"),
                        "title": res.get("title", "Video"),
                        "size": res.get("size", 0)
                    }
        except Exception as e:
            if i == retries - 1: raise e
            await asyncio.sleep(1)
    return None
