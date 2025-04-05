from datetime import datetime
import re

def read_file_content(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def write_file_content(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def update_readme(filename, stats):
    content = read_file_content(filename)

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
        str(stats['http_count']),
        content
    )
    content = re.sub(
        r'{{\s*https_count\s*}}',
        str(stats['https_count']),
        content
    )
    content = re.sub(
        r'{{\s*socks4_count\s*}}',
        str(stats['socks4_count']),
        content
    )
    content = re.sub(
        r'{{\s*socks5_count\s*}}',
        str(stats['socks5_count']),
        content
    )
    
    write_file_content(filename, content)

def get_stats():
    stats = {
        'new_proxies_count': 0,
        'last_update_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
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
        stats['new_proxies_count'] = 0

    return stats

def main():
    stats = get_stats()

    update_readme('README.md', stats.copy())
    update_readme('README_ru.md', stats.copy())

if __name__ == '__main__':
    main()
