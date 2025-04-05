from datetime import datetime
import re

def get_stats():
    stats = {
        'new_proxies_count': 0,
        'last_update_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        'http_count': 0,
        'https_count': 0,
        'socks4_count': 0,
        'socks5_count': 0,
    }

    for proto in ['HTTP', 'HTTPS', 'Socks4', 'Socks5']:
        try:
            with open(f'{proto}.txt', 'r') as f:
                stats[f'{proto.lower()}_count'] = sum(1 for _ in f)
        except FileNotFoundError:
            stats[f'{proto.lower()}_count'] = 0

    try:
        with open('new_proxies_count.tmp', 'r') as f:
            stats['new_proxies_count'] = int(f.read().strip())
    except:
        pass

    return stats

def update_file(filename, patterns):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    for pattern, value in patterns.items():
        content = re.sub(pattern, str(value), content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    stats = get_stats()

    update_file('README.md', {
        r'{{ new_proxies_count }}': stats['new_proxies_count'],
        r'{{ last_update_time }}': stats['last_update_time'],
        r'{{ http_count }}': stats['http_count'],
        r'{{ https_count }}': stats['https_count'],
        r'{{ socks4_count }}': stats['socks4_count'],
        r'{{ socks5_count }}': stats['socks5_count'],
    })

    update_file('README_ru.md', {
        r'{{ new_proxies_count }}': stats['new_proxies_count'],
        r'{{ last_update_time }}': stats['last_update_time'],
        r'{{ http_count }}': stats['http_count'],
        r'{{ https_count }}': stats['https_count'],
        r'{{ socks4_count }}': stats['socks4_count'],
        r'{{ socks5_count }}': stats['socks5_count'],
    })

if __name__ == '__main__':
    main()
