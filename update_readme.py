from datetime import datetime
import os

def get_new_proxies_count():
    try:
        with open('new_proxies_count.txt', 'r') as f:
            return int(f.read().strip())
    except:
        return 0

def get_proxy_counts():
    counts = {}
    for proto in ['HTTP', 'HTTPS', 'Socks4', 'Socks5']:
        try:
            with open(f'{proto}.txt', 'r') as f:
                counts[proto.lower() + '_count'] = sum(1 for _ in f)
        except:
            counts[proto.lower() + '_count'] = 0
    return counts

def update_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = {
        'new_proxies_count': get_new_proxies_count(),
        'last_update_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        **get_proxy_counts()
    }

    for key, value in replacements.items():
        content = content.replace(f'{{{{ {key} }}}}', str(value))

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_readme()
