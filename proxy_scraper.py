import os
import asyncio
import aiohttp

PROXY_SOURCES = os.getenv("PROXY_SOURCES", "").split(",")
PROXY_TIMEOUT = 5 
TEST_URL = "http://google.com"

OUTPUT_FILES = {
    "ALL": "All.txt",
    "HTTP": "HTTP.txt",
    "HTTPS": "HTTPS.txt",
    "SOCKS4": "Socks4.txt",
    "SOCKS5": "Socks5.txt",
}


async def fetch_proxies():
    proxies = set()
    async with aiohttp.ClientSession() as session:
        tasks = [download_proxies(session, url) for url in PROXY_SOURCES if url.strip()]
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)

    return list(proxies)


async def download_proxies(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                content = await response.text()

                try:
                    json_data = await response.json()
                    if "data" in json_data:
                        return parse_json_proxies(json_data["data"])
                except:
                    pass

                return set(content.strip().split("\n"))

    except Exception as e:
        print(f"Error loading {url}: {e}")
    return set()


def parse_json_proxies(data):
    proxies = set()
    for item in data:
        ip = item.get("ip")
        port = item.get("port")
        protocols = item.get("protocols", [])
        if ip and port:
            for protocol in protocols:
                protocol = protocol.upper()
                if protocol in OUTPUT_FILES:
                    proxies.add(f"{ip}:{port}")
    return proxies


async def check_proxy(session, proxy):
    proxy_types = {
        "HTTP": f"http://{proxy}",
        "HTTPS": f"https://{proxy}",
        "SOCKS4": f"socks4://{proxy}",
        "SOCKS5": f"socks5://{proxy}",
    }

    for ptype, purl in proxy_types.items():
        proxies = {"http": purl, "https": purl}
        try:
            async with session.get(TEST_URL, proxy=proxies["http"], timeout=PROXY_TIMEOUT) as response:
                if response.status == 200:
                    print(f"✅ Working {ptype} proxy: {proxy}")
                    return ptype, proxy
        except:
            pass

    print(f"❌ Proxy {proxy} is not working.")
    return None, None


async def sort_and_save_proxies(proxies):
    sorted_proxies = {key: set() for key in OUTPUT_FILES.keys()}
    
    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(session, proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)

    for ptype, proxy in results:
        if ptype and proxy:
            sorted_proxies["ALL"].add(proxy)
            sorted_proxies[ptype].add(proxy)

    for key, filename in OUTPUT_FILES.items():
        with open(filename, "w") as f:
            f.write("\n".join(sorted_proxies[key]))
    
    print("✅ Proxies successfully saved!")


async def main():
    print("🚀 Starting proxy collection and verification...")
    proxies = await fetch_proxies()
    await sort_and_save_proxies(proxies)
    print("🎉 Done!")


if __name__ == "__main__":
    asyncio.run(main())
