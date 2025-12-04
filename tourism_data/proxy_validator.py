# proxy_validator.py (Multi-Source Ultimate Version)

import requests
from bs4 import BeautifulSoup
import concurrent.futures
import random
import re

# --- 配置区 ---

# 【升级】定义多个代理IP来源网站
PROXY_SOURCES = [
    {'url': 'https://www.89ip.cn/', 'parser': 'parse_89ip'},
    {'url': 'https://www.kuaidaili.com/free/inha/', 'parser': 'parse_kuaidaili'},
    {'url': 'http://www.ip3366.net/free/', 'parser': 'parse_ip3366'},
    # 您可以继续添加更多来源
]

VALIDATION_URL = 'http://httpbin.org/ip'
TIMEOUT = 5
OUTPUT_FILE = 'proxies.txt'
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
]


# --- 针对不同网站的解析函数 ---

def parse_89ip(html):
    """解析 89ip.cn 的页面"""
    soup = BeautifulSoup(html, 'lxml')
    rows = soup.select('table.layui-table tbody tr')
    proxies = []
    for row in rows:
        ip = row.select_one('td:nth-child(1)').get_text(strip=True)
        port = row.select_one('td:nth-child(2)').get_text(strip=True)
        if ip and port:
            proxies.append(f'{ip}:{port}')
    return proxies


def parse_kuaidaili(html):
    """解析 kuaidaili.com 的页面"""
    soup = BeautifulSoup(html, 'lxml')
    rows = soup.select('table.table-bordered tbody tr')
    proxies = []
    for row in rows:
        ip = row.select_one('td[data-title="IP"]').get_text(strip=True)
        port = row.select_one('td[data-title="PORT"]').get_text(strip=True)
        if ip and port:
            proxies.append(f'{ip}:{port}')
    return proxies


def parse_ip3366(html):
    """解析 ip3366.net 的页面"""
    soup = BeautifulSoup(html, 'lxml')
    rows = soup.select('#list table tbody tr')
    proxies = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            ip = cells[0].get_text(strip=True)
            port = cells[1].get_text(strip=True)
            if ip and port:
                proxies.append(f'{ip}:{port}')
    return proxies


# --- 主逻辑 ---

def fetch_proxies_from_source(source):
    """从单个源抓取代理"""
    url = source['url']
    parser_func_name = source['parser']
    parser_func = globals()[parser_func_name]

    print(f"[*] 正在从 {url} 获取代理列表...")
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return parser_func(response.text)
    except Exception as e:
        print(f"[!] 从 {url} 获取代理失败: {e}")
        return []


def validate_proxy(proxy):
    """验证单个代理的可用性"""
    proxy_dict = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(VALIDATION_URL, headers=headers, proxies=proxy_dict, timeout=TIMEOUT)
        response.raise_for_status()
        # 确认返回的IP确实是代理IP
        if proxy.split(':')[0] in response.json().get('origin', ''):
            print(f"  [成功] 代理 {proxy} 可用")
            return proxy
    except Exception:
        return None


if __name__ == '__main__':
    all_raw_proxies = set()  # 使用集合来自动去重

    # 1. 从所有源并发获取原始代理列表
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PROXY_SOURCES)) as executor:
        future_to_source = {executor.submit(fetch_proxies_from_source, source): source for source in PROXY_SOURCES}
        for future in concurrent.futures.as_completed(future_to_source):
            proxies = future.result()
            if proxies:
                all_raw_proxies.update(proxies)

    print(f"\n[*] 从所有来源共获取 {len(all_raw_proxies)} 个不重复的代理IP，准备开始验证...")

    if all_raw_proxies:
        valid_proxies = []
        # 2. 使用多线程并发验证
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            future_to_proxy = {executor.submit(validate_proxy, proxy): proxy for proxy in all_raw_proxies}
            for future in concurrent.futures.as_completed(future_to_proxy):
                result = future.result()
                if result:
                    valid_proxies.append(result)

        # 3. 将所有验证通过的代理IP写入文件
        print(f"\n[*] 验证完成！共找到 {len(valid_proxies)} 个可用代理。")
        if valid_proxies:
            with open(OUTPUT_FILE, 'w') as f:
                for proxy in valid_proxies:
                    f.write(f"http://{proxy}\n")
            print(f"[*] 可用代理已保存到文件: {OUTPUT_FILE}")
        else:
            print("[!] 本次运行未找到任何可用的代理IP。请稍后重试或更换代理源。")