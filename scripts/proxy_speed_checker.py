import asyncio
import aiohttp
import os
import json
import time

PROXY_DIR = "."
OUTPUT_FILE = "public/results.json"
TIMEOUT = 10
TEST_URL = "http://google.com"

async def test_proxy(session, proxy, proxy_type):
    try:
        start = time.monotonic()
        async with session.get(TEST_URL, proxy=f"{proxy_type}://{proxy}", timeout=TIMEOUT) as resp:
            if resp.status == 200:
                duration = round(time.monotonic() - start, 2)
                return proxy, duration
    except Exception:
        return proxy, None

async def check_file(filename):
    proxy_type = filename.replace(".txt", "")
    proxies = []

    with open(filename, "r") as f:
        for line in f:
            proxy = line.strip()
            if proxy:
                proxies.append(proxy)

    results = []
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [test_proxy(session, proxy, proxy_type) for proxy in proxies]
        for fut in asyncio.as_completed(tasks):
            proxy, delay = await fut
            results.append({
                "proxy": proxy,
                "type": proxy_type,
                "delay": delay
            })
    
    return results

async def main():
    os.makedirs("public", exist_ok=True)
    all_results = []

    for file in os.listdir(PROXY_DIR):
        if file.endswith(".txt") and file != "All.txt":
            print(f"Checking {file}")
            res = await check_file(os.path.join(PROXY_DIR, file))
            all_results.extend(res)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
