"""
爬虫请求模块
负责发起HTTP请求，获取网页内容
"""
import requests
import time
import random
from typing import List, Dict
from requests.adapters import HTTPAdapter
from requests.exceptions import SSLError
from urllib3.util.retry import Retry
from .config import HEADERS, REQUEST_TIMEOUT, MAX_PAGES, SIMULATED_PRODUCTS, BASE_URL, PAGINATION_PARAMS

# 全局Session，启用重试策略
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)


def fetch_page(url: str) -> str:
    """
    获取指定URL的页面内容
    
    Args:
        url: 目标页面URL
        
    Returns:
        页面HTML内容
    """
    try:
        # 添加随机延时，避免过于频繁的请求
        time.sleep(random.uniform(0.5, 1.5))

        response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except SSLError as e:
        print(f"SSL错误: {e}")
        # 回退：尝试使用 http 或关闭证书验证（谨慎）
        try:
            if url.startswith('https://'):
                fallback = 'http://' + url[len('https://'):]
                print(f"尝试回退到 HTTP: {fallback}")
                response = session.get(fallback, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response.text
        except Exception:
            pass

        try:
            print("尝试使用 verify=False 再次请求（不推荐，仅作回退）")
            response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e2:
            print(f"回退请求仍失败: {e2}")
            return ''
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return ""


def handle_request_exception(func):
    """
    装饰器：处理请求异常
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout:
            print("请求超时")
            return None
        except requests.exceptions.ConnectionError:
            print("连接错误")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误: {e}")
            return None
        except Exception as e:
            print(f"其他错误: {e}")
            return None
    return wrapper


def crawl_all_pages() -> List[Dict]:
    """
    爬取所有页面的商品数据
    优先尝试爬取真实网站数据，如果失败则使用模拟数据
    
    Returns:
        商品数据列表
    """
    print("开始爬取商品数据...")
    
    # 尝试爬取真实网站数据
    all_products = []
    
    # 尝试爬取前几页真实数据
    successful_crawls = 0
    for page in range(1, MAX_PAGES + 1):
        print(f"正在爬取第 {page} 页...")
        
        # 构建页面URL - books.toscrape.com的分页URL格式为catalogue/page-2.html
        if page == 1:
            page_url = f"{BASE_URL}"
        else:
            page_url = f"{BASE_URL}catalogue/page-{page}.html"
        
        html_content = fetch_page(page_url)
        
        if html_content:
            # 尝试解析页面内容
            from .parser import parse_product_list
            page_products = parse_product_list(html_content)
            
            if page_products:
                # 如果成功解析到商品数据，添加到总列表
                all_products.extend(page_products)
                successful_crawls += 1
                print(f"第 {page} 页爬取成功，获取 {len(page_products)} 个商品")
            else:
                print(f"第 {page} 页解析失败，使用模拟数据")
        else:
            print(f"第 {page} 页请求失败")
        
        # 模拟实际爬取过程中的延时
        time.sleep(0.5)
    
    # 如果没有成功爬取到任何真实数据，则使用模拟数据
    if successful_crawls == 0:
        print("真实网站爬取失败，切换到模拟数据模式...")
        
        for page in range(1, MAX_PAGES + 1):
            print(f"正在生成第 {page} 页模拟数据...")
            
            # 为每页生成不同的模拟数据
            page_products = []
            for i, product in enumerate(SIMULATED_PRODUCTS):
                # 为不同页面创建略有差异的商品数据
                new_product = product.copy()
                new_product['name'] = f"{product['name']}_{page}_{i+1}"
                new_product['price'] = round(product['price'] * (1 + (page-1) * 0.02), 2)  # 每页价格略有浮动
                new_product['sales'] = product['sales'] + (page-1) * 100  # 每页销量略有增加
                page_products.append(new_product)
            
            all_products.extend(page_products)
            print(f"第 {page} 页模拟数据生成完成，共 {len(page_products)} 个商品")
    
    print(f"爬取完成，共获取 {len(all_products)} 个商品数据")
    return all_products