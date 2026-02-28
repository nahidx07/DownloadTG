import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_media(url: str):
    # আমরা বিভিন্ন Cobalt Instance ট্রাই করবো যদি একটি ফেইল করে
    api_instances = [
        "https://api.cobalt.tools/",
        "https://cobalt-api.v0l.io/"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url,
        "videoQuality": "720",
        "filenameStyle": "basic",
        "downloadMode": "video"
    }

    for api_url in api_instances:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.post(api_url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"API {api_url} error: {response.status_code}")
                    continue
                
                data = response.json()
                status = data.get("status")

                # Cobalt API বিভিন্ন ফরম্যাটে লিঙ্ক দেয়
                if status in ["stream", "redirect", "video"]:
                    return {"url": data.get("url"), "title": "Downloaded Video"}
                
                elif status == "picker":
                    # যদি মাল্টিপল কোয়ালিটি থাকে, তবে প্রথমটি নেওয়া
                    return {"url": data["picker"][0].get("url"), "title": "Downloaded Video"}
                
                elif status == "error":
                    logger.warning(f"Cobalt Error from {api_url}: {data.get('text')}")
                    continue

        except Exception as e:
            logger.error(f"Request failed for {api_url}: {e}")
            continue
            
    return None
