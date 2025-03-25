import os
import asyncio
import aiohttp
from aiohttp_socks import SocksConnector

PROXY_SOURCES = os.getenv("PROXY_SOURCES", "").split(",")
PROXY_TIMEOUT = 5
TEST_URL = "https://httpbin.org/ip"

OUTPUT_FILES = {
    "ALL": "All.txt",
    "HTTP": "HTTP.txt",
    "HTTPS": "HTTPS.txt",
    "SOCKS4": "Socks4.txt",
    "SOCKS5": "Socks5.txt",
}

async def fetch_proxies():
    proxies = set()
    sources = [url.strip() for url in PROXY_SOURCES if url.strip()]
    if not sources:
        print("⚠️ No proxy sources configured!")
        return []

    print(f"🔄 Fetching proxies from {len(sources)} sources...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [download_proxies(session, url) for url in sources]
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)

    print(f"✅ Total {len(proxies)} proxies found")
    return list(proxies)

async def download_proxies(session, url):
    try:
        print(f"⏬ Downloading from {url}")
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                
                if 'json' in content_type:
                    try:
                        json_data = await response.json()
                        return parse_json_proxies(json_data)
                    except Exception as e:
                        print(f"⚠️ JSON parse error in {url}: {e}")
                
                text_data = await response.text()
                return set(line.strip() for line in text_data.splitlines() if line.strip())

    except Exception as e:
        print(f"⚠️ Error loading {url}: {str(e)[:100]}")
    return set()

def parse_json_proxies(data):
    proxies = set()
    items = data.get("data", data.get("proxies", data))
    
    if isinstance(items, dict):
        items = items.values()
    
    for item in items:
        try:
            ip = item.get("ip", item.get("host"))
            port = str(item.get("port"))
            
            if not ip or not port:
                continue
                
            proxy = f"{ip}:{port}"
            protocols = item.get("protocols", item.get("type", []))
            if isinstance(protocols, str):
                protocols = [protocols.upper()]
            else:
                protocols = [p.upper() for p in protocols]
            
            for proto in protocols:
                if proto in OUTPUT_FILES:
                    proxies.add(proxy)
                    break

        except Exception as e:
            print(f"⚠️ Error parsing proxy item: {e}")
    
    return proxies

async def check_proxy(session, proxy):
    test_proxies = {
        "HTTP": f"http://{proxy}",
        "HTTPS": f"http://{proxy}",
        "SOCKS4": f"socks4://{proxy}",
        "SOCKS5": f"socks5://{proxy}",
    }

    for ptype, purl in test_proxies.items():
        try:
            connector = None
            if ptype.startswith("SOCKS"):
                connector = SocksConnector.from_url(purl)
                test_session = aiohttp.ClientSession(connector=connector)
            else:
                test_session = session

            async with test_session.get(
                TEST_URL,
                timeout=PROXY_TIMEOUT,
                ssl=False
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "origin" in data:
                        print(f"✅ Working {ptype} proxy: {proxy}")
                        return ptype, proxy
        except Exception as e:
            pass
        finally:
            if connector:
                await test_session.close()

    print(f"❌ Proxy {proxy} failed all checks")
    return None, None

async def sort_and_save_proxies(proxies):
    sorted_proxies = {key: set() for key in OUTPUT_FILES.keys()}
    
    print(f"🔍 Checking {len(proxies)} proxies...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(session, proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        ptype, proxy = result
        if ptype and proxy:
            sorted_proxies["ALL"].add(proxy)
            sorted_proxies[ptype].add(proxy)

    for key, filename in OUTPUT_FILES.items():
        count = len(sorted_proxies[key])
        print(f"💾 Saving {count} {key} proxies to {filename}")
        with open(filename, "w") as f:
            f.write("\n".join(sorted(sorted_proxies[key])))
    
    print("✅ All proxies processed!")

async def main():
    print("🚀 Starting proxy scraper...")
    proxies = await fetch_proxies()
    if proxies:
        await sort_and_save_proxies(proxies)
    else:
        print("⚠️ No proxies to check!")
    print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(main())
