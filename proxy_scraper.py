import os
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from aiohttp import BasicAuth
import re

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
    
    async with aiohttp.ClientSession() as session:
        tasks = [download_proxies(session, url) for url in sources]
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)

    print(f"✅ Found {len(proxies)} proxies")
    return list(proxies)

async def download_proxies(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                
                if 'json' in content_type:
                    try:
                        json_data = await response.json()
                        return parse_json_proxies(json_data)
                    except Exception as e:
                        print(f"⚠️ JSON parsing error in {url}: {e}")
                
                text_data = await response.text()
                return set(line.strip() for line in text_data.splitlines() if line.strip())

    except aiohttp.ClientTimeout:
        print(f"⚠️ Timeout loading {url}")
    except aiohttp.ClientConnectionError:
        print(f"⚠️ Connection error for {url}")
    except Exception as e:
        print(f"⚠️ Unexpected error loading {url}: {e}")
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
    proxy_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$")
    if not proxy_pattern.match(proxy):
        print(f"⚠️ Invalid proxy format: {proxy}")
        return [], None

    test_proxies = {
        "HTTP": f"http://{proxy}",
        "HTTPS": f"http://{proxy}",
        "SOCKS4": f"socks4://{proxy}",
        "SOCKS5": f"socks5://{proxy}",
    }

    working_protocols = []
    for ptype, purl in test_proxies.items():
        try:
            connector = None
            if ptype.startswith("SOCKS"):
                connector = ProxyConnector.from_url(purl)
                test_session = aiohttp.ClientSession(connector=connector)
            else:
                test_session = session

            if "@" in proxy:
                auth, ip_port = proxy.split("@")
                username, password = auth.split(":")
                proxy_url = f"{ptype.lower()}://{ip_port}"
                auth = BasicAuth(username, password)
                async with test_session.get(TEST_URL, proxy=proxy_url, proxy_auth=auth, timeout=PROXY_TIMEOUT) as response:
                    if response.status == 200 and "origin" in await response.json():
                        working_protocols.append(ptype)
            else:
                async with test_session.get(TEST_URL, proxy=purl, timeout=PROXY_TIMEOUT) as response:
                    if response.status == 200 and "origin" in await response.json():
                        working_protocols.append(ptype)
        except Exception:
            pass
        finally:
            if connector:
                await test_session.close()

    if working_protocols:
        print(f"✅ Working proxy: {proxy} (protocols: {', '.join(working_protocols)})")
        return working_protocols, proxy
    else:
        print(f"❌ Proxy {proxy} failed all checks")
        return [], None

async def sort_and_save_proxies(proxies):
    sorted_proxies = {key: set() for key in OUTPUT_FILES.keys()}
    
    print(f"🔍 Checking {len(proxies)} proxies...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(session, proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        ptypes, proxy = result
        if ptypes and proxy:
            sorted_proxies["ALL"].add(proxy)
            for ptype in ptypes:
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
