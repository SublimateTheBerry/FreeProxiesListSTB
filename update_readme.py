from datetime import datetime
import re

def update_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return

    stats = {
        'new_proxies_count': 0,
        'last_update_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
    }
    
    for proto in ['HTTP', 'HTTPS', 'Socks4', 'Socks5']:
        try:
            with open(f'{proto}.txt', 'r') as f:
                stats[f'{proto.lower()}_count'] = sum(1 for _ in f)
        except:
            stats[f'{proto.lower()}_count'] = 0

    try:
        with open('new_proxies_count.tmp', 'r') as f:
            stats['new_proxies_count'] = int(f.read().strip())
    except:
        stats['new_proxies_count'] = 0

    content = re.sub(
        r'{{\s*new_proxies_count\s*}}',
        str(stats['new_proxies_count']),
        content
    )
    content = re.sub(
        r'{{\s*last_update_time\s*}}',
        stats['last_update_time'],
        content
    )
    content = re.sub(
        r'{{\s*http_count\s*}}',
        str(stats.get('http_count', 0)),
        content
    )
    content = re.sub(
        r'{{\s*https_count\s*}}',
        str(stats.get('https_count', 0)),
        content
    )
    content = re.sub(
        r'{{\s*socks4_count\s*}}',
        str(stats.get('socks4_count', 0)),
        content
    )
    content = re.sub(
        r'{{\s*socks5_count\s*}}',
        str(stats.get('socks5_count', 0)),
        content
    )

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_file('README.md')
    update_file('README_ru.md')
