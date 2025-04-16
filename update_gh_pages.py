#!/usr/bin/env python3
import json
from datetime import datetime

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FreeProxiesSTB - Sorted by Speed</title>
  <style>
    /* Global Styles */
    body {{
      background-color: #121212;
      color: #ffffff;
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 800px;
      margin: 30px auto;
      padding: 20px;
      border: 1px solid #ffffff;
      border-radius: 8px;
      background-color: #1e1e1e;
    }}
    h1 {{
      text-align: center;
      margin-top: 0;
      font-size: 2em;
    }}
    .proxy-category {{
      margin-bottom: 20px;
      padding: 10px;
      border: 1px solid #ffffff;
      border-radius: 8px;
    }}
    .proxy-header {{
      font-size: 1.2em;
      text-align: center;
      padding-bottom: 5px;
      margin-bottom: 10px;
      border-bottom: 1px dashed #ffffff;
    }}
    .proxy-list {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}
    .proxy-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 5px 0;
      border-bottom: 1px solid #ffffff;
    }}
    .proxy-item:last-child {{
      border-bottom: none;
    }}
    .copy-btn {{
      background-color: transparent;
      border: 1px solid #ffffff;
      color: #ffffff;
      cursor: pointer;
      padding: 5px 10px;
      border-radius: 4px;
      transition: background-color 0.3s ease, color 0.3s ease;
    }}
    .copy-btn:hover {{
      background-color: #ffffff;
      color: #121212;
    }}
    .stats, .copyright {{
      text-align: center;
      font-size: 0.9em;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>
  <a href="https://github.com/SublimateTheBerry/FreeProxiesListSTB" style="color: #ffffff; text-decoration: none;">FreeProxiesSTB - Sorted by Speed</a>
    </h1>

    
    <!-- HTTP/HTTPS Proxies -->
    <div class="proxy-category" id="http-https-proxies">
      <div class="proxy-header">HTTP/HTTPS Proxies</div>
      <ul class="proxy-list">
        {http_https_list}
      </ul>
    </div>
    
    <!-- SOCKS4 Proxies -->
    <div class="proxy-category" id="socks4-proxies">
      <div class="proxy-header">SOCKS4 Proxies</div>
      <ul class="proxy-list">
        {socks4_list}
      </ul>
    </div>
    
    <!-- SOCKS5 Proxies -->
    <div class="proxy-category" id="socks5-proxies">
      <div class="proxy-header">SOCKS5 Proxies</div>
      <ul class="proxy-list">
        {socks5_list}
      </ul>
    </div>
    
    <!-- Statistics and Copyright -->
    <div class="stats">
      Last update: {last_update}
    </div>
    <div class="copyright">
      &copy; 2025 <a href="https://github.com/SublimateTheBerry" style="color: #888; font-weight: bold; text-decoration: none;">SublimateTheBerry</a>
    </div>
  </div>
  
  <script>
    // Copy-to-Clipboard функционал для всех кнопок
    document.querySelectorAll('.copy-btn').forEach(button => {{
      button.addEventListener('click', function() {{
        const textToCopy = this.getAttribute('data-text');
        navigator.clipboard.writeText(textToCopy).then(() => {{
          const original = this.textContent;
          this.textContent = 'Copied!';
          setTimeout(() => {{ this.textContent = original; }}, 1500);
        }}).catch(err => {{
          console.error('Could not copy text: ', err);
        }});
      }});
    }});
  </script>
</body>
</html>
"""

def generate_list_items(proxy_results):
    items = []
    for proxy_info in proxy_results:
        proxy = proxy_info.get("proxy", "")
        speed = proxy_info.get("speed", 0)
        # Отображаем текст с информацией о скорости, но копируется только "ip:port"
        item_html = f'''<li class="proxy-item">
  <span class="proxy-text">{proxy} - {speed}ms</span>
  <button class="copy-btn" data-text="{proxy}">Copy</button>
</li>'''
        items.append(item_html)
    return "\n".join(items)

def main():
    try:
        with open("speed_results.json", "r") as f:
            results = json.load(f)
    except Exception as e:
        print(f"Ошибка чтения speed_results.json: {e}")
        results = {}

    # Объединяем HTTP и HTTPS прокси
    combined_http_https = results.get("http", []) + results.get("https", [])
    # При необходимости сортируем по скорости (возрастанию)
    combined_http_https.sort(key=lambda x: x.get("speed", float('inf')))
    http_https_list = generate_list_items(combined_http_https)

    # SOCKS4 и SOCKS5 оставляем в отдельных категориях
    socks4_list = generate_list_items(results.get("socks4", []))
    socks5_list = generate_list_items(results.get("socks5", []))
    
    last_update = datetime.now().strftime("%B %d, %Y, %H:%M")
    
    html_content = HTML_TEMPLATE.format(
        http_https_list=http_https_list,
        socks4_list=socks4_list,
        socks5_list=socks5_list,
        last_update=last_update
    )
    
    with open("index.html", "w") as f:
        f.write(html_content)
    
    print("index.html обновлен с последними результатами тестирования скорости прокси.")

if __name__ == "__main__":
    main()
