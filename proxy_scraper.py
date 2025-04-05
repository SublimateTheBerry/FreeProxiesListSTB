import os
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
import re
import random
import time
from datetime import datetime

PROXY_TIMEOUT = 10
TEST_URL = "https://httpbin.org/ip"
PROXY_SOURCES = os.getenv("PROXY_SOURCES", "").split(",")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/12345",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
]

OUTPUT_FILES = {
    "ALL": "All.txt",
    "HTTP": "HTTP.txt",
    "HTTPS": "HTTPS.txt",
    "SOCKS4": "Socks4.txt",
    "SOCKS5": "Socks5.txt",
}

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://google.com",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }

async def search_duckduckgo(session):
    proxies = set()
    query = "free proxy list -inurl:(signup|login) site:*.org|*.net|*.com"
    url = f"https://duckduckgo.com/html/?q={query}"
    
    try:
        headers = get_random_headers()
        await asyncio.sleep(random.uniform(1, 3))
        
        response = await session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(await response.text(), "html.parser")
        links = [a["href"] for a in soup.select("a.result__url")[:10]]
        print(f"🔍 Found {len(links)} links from DuckDuckGo")
        
        tasks = [download_proxies(session, link) for link in links]
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)
    except Exception as e:
        print(f"⚠️ DuckDuckGo error: {e}")
    
    return proxies

async def search_google(session):
    proxies = set()
    query = "free proxy list -inurl:(signup|login) site:*.org|*.net|*.com"
    params = {
        "q": query.replace(" ", "+"),
        "num": "10",
        "gl": random.choice(["US", "DE", "FR", "GB"]),
        "hl": random.choice(["en", "ru", "de"]),
        "safe": "off",
        "start": random.randint(0, 20)
    }
    url = "https://www.google.com/search"
    
    try:
        headers = get_random_headers()
        await asyncio.sleep(random.uniform(1, 3))
        
        response = await session.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(await response.text(), "html.parser")
        links = [a["href"] for a in soup.select("a.yuRUbf")[:10]]
        print(f"🔍 Found {len(links)} links from Google")
        
        tasks = [download_proxies(session, link) for link in links]
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)
    except Exception as e:
        print(f"⚠️ Google error: {e}")
    
    return proxies

async def search_yandex(session):
    proxies = set()
    query = "free proxy list -site:signup -site:login"
    params = {
        "text": query.replace(" ", "+"),
        "numdoc": "10",
        "lr": random.choice(["1", "2", "3"]),
        "p": random.randint(0, 50),
        "msid": f"yandex_search_{int(time.time())}"
    }
    url = "https://yandex.ru/search/"
    
    try:
        headers = get_random_headers()
        await asyncio.sleep(random.uniform(1, 3))
        
        response = await session.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(await response.text(), "html.parser")
        links = [a["href"] for a in soup.select(".link__url")[:10]]
        print(f"🔍 Found {len(links)} links from Yandex")
        
        tasks = [download_proxies(session, link) for link in links]
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)
    except Exception as e:
        print(f"⚠️ Yandex error: {e}")
    
    return proxies

async def fetch_proxies():
    proxies = set()
    
    async with aiohttp.ClientSession() as session:
        if PROXY_SOURCES:
            tasks = [download_proxies(session, url) for url in PROXY_SOURCES]
            results = await asyncio.gather(*tasks)
            for res in results:
                proxies.update(res)
            print(f"✅ Collected {len(proxies)} proxies from sources")
        
        search_tasks = [
            search_duckduckgo(session),
            search_google(session),
            search_yandex(session)
        ]
        
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        for result in search_results:
            if isinstance(result, Exception):
                continue
            proxies.update(result)
        
        print(f"✅ Total unique proxies: {len(proxies)}")
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
        print(f"⚠️ Download error for {url}: {str(e)[:50]}")
    
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
    
    async def test_protocol(proto):
        try:
            connector = None
            if proto.startswith('socks'):
                connector = ProxyConnector.from_url(f"{proto}://{proxy_url}", limit=0)
            else:
                connector = ProxyConnector.from_url(f"http://{proxy_url}", limit=0)
            
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
    print("🚀 Starting proxy collector...")
    proxies = await fetch_proxies()
    if proxies:
        await sort_and_save_proxies(proxies)
    else:
        print("⚠️ Proxies not found!")
    print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(main())
