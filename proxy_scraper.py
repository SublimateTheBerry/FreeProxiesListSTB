import os
import requests
import re

def fetch_proxies(urls):
    proxies = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxies.update(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text))
        except requests.RequestException:
            print(f"Не удалось загрузить прокси с {url}")
    return proxies

def categorize_proxies(proxies):
    http_proxies, https_proxies, socks4_proxies, socks5_proxies = set(), set(), set(), set()
    for proxy in proxies:
        if proxy.endswith(':80') or proxy.endswith(':8080'):
            http_proxies.add(proxy)
        elif proxy.endswith(':443'):
            https_proxies.add(proxy)
        elif proxy.endswith(':1080'):
            socks5_proxies.add(proxy)
        else:
            socks4_proxies.add(proxy)
    return http_proxies, https_proxies, socks4_proxies, socks5_proxies

def save_proxies(filename, proxies):
    with open(filename, 'w') as f:
        f.write('\n'.join(proxies))

if __name__ == "__main__":
    proxy_sources = os.getenv("PROXY_SOURCES", "").split(",")
    proxies = fetch_proxies(proxy_sources)
    
    http, https, socks4, socks5 = categorize_proxies(proxies)
    save_proxies("All.txt", proxies)
    save_proxies("HTTP.txt", http)
    save_proxies("HTTPS.txt", https)
    save_proxies("Socks4.txt", socks4)
    save_proxies("Socks5.txt", socks5)
    print("Готово! Прокси обновлены.")
