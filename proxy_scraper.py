import os
import asyncio
import aiohttp

# Настройки
PROXY_SOURCES = os.getenv("PROXY_SOURCES", "").split(",")  # Список источников прокси
PROXY_TIMEOUT = 5  # Таймаут проверки прокси (сек)
TEST_URL = "http://google.com"  # Сайт для проверки

# Файлы для сохранения
OUTPUT_FILES = {
    "ALL": "All.txt",
    "HTTP": "HTTP.txt",
    "HTTPS": "HTTPS.txt",
    "SOCKS4": "Socks4.txt",
    "SOCKS5": "Socks5.txt",
}


async def fetch_proxies():
    """Собирает прокси со всех источников."""
    proxies = set()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in PROXY_SOURCES:
            url = url.strip()
            if url:
                tasks.append(download_proxies(session, url))
        
        results = await asyncio.gather(*tasks)
        for res in results:
            proxies.update(res)

    return list(proxies)


async def download_proxies(session, url):
    """Загружает список прокси с одного источника."""
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return set(response.text.strip().split("\n"))
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
    return set()


async def check_proxy(session, proxy):
    """Проверяет работоспособность прокси."""
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
                    print(f"✅ Рабочий {ptype} прокси: {proxy}")
                    return ptype, proxy
        except:
            pass

    print(f"❌ Прокси {proxy} не работает.")
    return None, None


async def sort_and_save_proxies(proxies):
    """Сортирует прокси по типам и сохраняет в файлы."""
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
    
    print("✅ Прокси успешно сохранены!")


async def main():
    print("🚀 Начинаем сбор и проверку прокси...")
    proxies = await fetch_proxies()
    await sort_and_save_proxies(proxies)
    print("🎉 Готово!")


if __name__ == "__main__":
    asyncio.run(main())
