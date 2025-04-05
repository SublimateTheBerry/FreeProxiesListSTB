import os
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
import re
from datetime import datetime

PROXY_TIMEOUT = 10
TEST_URL = "https://httpbin.org/ip"
PROXY_SOURCES = os.getenv("PROXY_SOURCES", "").split(",")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

OUTPUT_FILES = {
    "ALL": "All.txt",
    "HTTP": "HTTP.txt",
    "HTTPS": "HTTPS.txt",
    "SOCKS4": "Socks4.txt",
    "SOCKS5": "Socks5.txt",
}

async def search_duckduckgo():
    proxies = set()
    query = "free proxy list -inurl:(signup|login) site:*.org|*.net|*.com"
    url = f"https://duckduckgo.com/html/?q={query}"
    
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=15
            )
            response.raise_for_status()
            soup = BeautifulSoup(await response.text(), "html.parser")
            links = [a["href"] for a in soup.select("a.result__url")[:10]]
            print(f"🔍 Found {len(links)} DuckDuckGo links")
            
            tasks = [download_proxies(session, link) for link in links]
            results = await asyncio.gather(*tasks)
            for res in results:
                proxies.update(res)
        except Exception as e:
            print(f"⚠️ DuckDuckGo error: {e}")
    
    return proxies

async def fetch_proxies():
    proxies = set()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in PROXY_SOURCES:
            tasks.append(download_proxies(session, url))
        
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)
        
        print(f"✅ Collected {len(proxies)} proxies from sources")
        
        duckduckgo_proxies = await search_duckduckgo()
        proxies.update(duckduckgo_proxies)
        
        return list(proxies)

async def download_proxies(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                
                if 'json' in content_type:
                    try:
                        data = await response.json()
                        return parse_json_proxies(data)
                    except Exception as e:
                        print(f"⚠️ JSON error: {url} - {e}")
                
                text = await response.text()
                pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):(?:\d{2,5})\b'
                found = set(re.findall(pattern, text))
                return found
    except Exception as e:
        print(f"⚠️ Download error {url}: {str(e)[:50]}")
    
    return set()

def parse_json_proxies(data):
    proxies = set()
    items = data.get('proxies', data.get('data', data))
    
    if isinstance(items, list):
        for item in items:
            ip = item.get('ip', item.get('host'))
            port = item.get('port')
            if ip and port:
                proxy = f"{ip}:{port}"
                proxies.add(proxy)
    elif isinstance(items, dict):
        for key in items:
            proxy = f"{items[key].get('ip')}:{items[key].get('port')}"
            proxies.add(proxy)
    
    return proxies

async def check_proxy(session, proxy):
    valid_protocols = []
    proxy_url = proxy.split('@')[-1] if '@' in proxy else proxy
    ip_port = proxy_url.strip()
    
    async def test_protocol(proto):
        try:
            connector = None
            if proto.startswith('socks'):
                connector = ProxyConnector.from_url(f"{proto}://{ip_port}", limit=0)
            else:
                connector = ProxyConnector.from_url(f"http://{ip_port}", limit=0)
            
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT)) as test_session:
                async with test_session.get(TEST_URL) as resp:
                    if resp.status == 200 and (await resp.json()).get('origin'):
                        valid_protocols.append(proto.upper())
        except Exception as e:
            pass
    
    await asyncio.gather(
        test_protocol('http'),
        test_protocol('https'),
        test_protocol('socks4'),
        test_protocol('socks5')
    )
    
    return valid_protocols, proxy

async def sort_and_save_proxies(proxies):
    sorted_proxies = {k: set() for k in OUTPUT_FILES}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for proxy in proxies:
            tasks.append(check_proxy(session, proxy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                continue
            protocols, proxy_str = result
            if protocols:
                sorted_proxies["ALL"].add(proxy_str)
                for proto in protocols:
                    sorted_proxies[proto].add(proxy_str)
    
    for key, filename in OUTPUT_FILES.items():
        proxies_list = sorted(sorted_proxies[key])
        with open(filename, 'w') as f:
            f.write('\n'.join(proxies_list))
        print(f"💾 Saved {len(proxies_list)} {key} proxies to {filename}")
    
    with open('new_proxies_count.tmp', 'w') as f:
        f.write(str(len(sorted_proxies["ALL"])))

async def main():
    print("🚀 Starting proxy scraper...")
    proxies = await fetch_proxies()
    if proxies:
        await sort_and_save_proxies(proxies)
    else:
        print("⚠️ No proxies found!")
    print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(main())
