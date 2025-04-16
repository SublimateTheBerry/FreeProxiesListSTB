#!/usr/bin/env python3
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import glob
import os
import time
import json

REQUEST_TIMEOUT = 5  # секунд
HTTP_TEST_URL = "http://google.com"
HTTPS_TEST_URL = "https://google.com"

async def test_proxy(proxy: str, proxy_type: str) -> float:
    start_time = time.perf_counter()
    try:
        if proxy_type in ['http', 'https']:
            url = HTTP_TEST_URL if proxy_type == 'http' else HTTPS_TEST_URL
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as session:
                proxy_url = f"{proxy_type}://{proxy}"
                async with session.get(url, proxy=proxy_url) as response:
                    await response.text()  # ждём полный ответ
        elif proxy_type in ['socks4', 'socks5']:
            scheme = "socks4" if proxy_type == 'socks4' else "socks5"
            connector = ProxyConnector.from_url(f"{scheme}://{proxy}", limit=1, rdns=True)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as session:
                async with session.get(HTTP_TEST_URL) as response:
                    await response.text()
        else:
            return float('inf')
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000  # мс
        return round(latency, 2)
    except Exception:
        return float('inf')

async def test_proxy_with_sem(proxy: str, proxy_type: str, sem: asyncio.Semaphore) -> float:
    async with sem:
        return await test_proxy(proxy, proxy_type)

async def process_proxy_file(file_path: str, sem: asyncio.Semaphore) -> dict:
    base_name = os.path.basename(file_path)
    proxy_type = os.path.splitext(base_name)[0].lower()  # например, "http" из "http.txt"
    
    results = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Ошибка при чтении {file_path}: {e}")
        return {proxy_type: results}
    
    proxies = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    tasks = [test_proxy_with_sem(proxy, proxy_type, sem) for proxy in proxies]
    tested = await asyncio.gather(*tasks)
    
    for proxy, speed in zip(proxies, tested):
        if speed != float('inf'):
            results.append({"proxy": proxy, "speed": speed})
    results.sort(key=lambda x: x["speed"])  # сортируем по возрастанию скорости
    return {proxy_type: results}

async def main():
    # Находим все файлы *.txt, кроме "All.txt"
    proxy_files = glob.glob("*.txt")
    proxy_files = [f for f in proxy_files if os.path.basename(f).lower() != "all.txt"]
    
    sem = asyncio.Semaphore(10)  # ограничиваем число одновременных запросов
    tasks = [process_proxy_file(file, sem) for file in proxy_files]
    results_dict = {}
    file_results = await asyncio.gather(*tasks)
    for res in file_results:
        results_dict.update(res)
    
    with open("speed_results.json", "w") as outfile:
        json.dump(results_dict, outfile, indent=4)
    print("Speed tests completed. Results saved to speed_results.json.")

if __name__ == "__main__":
    asyncio.run(main())
