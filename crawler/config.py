"""
爬虫配置文件
定义爬虫相关的URL、请求头、分页参数等配置信息
"""

# 真实电商网站的基础URL（使用books.toscrape.com网站）
# 使用 HTTP 回退以避免本地环境中可能的 SSL 问题
BASE_URL = "http://books.toscrape.com/"

# 分页参数配置
PAGINATION_PARAMS = {
    "page": 1,  # 起始页码
    "limit": 20  # 每页商品数量
}

# 最大爬取页数
MAX_PAGES = 10  # 调整为10页以获取更多数据（总共约200本书）

# 请求头配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# 请求超时时间（秒）
REQUEST_TIMEOUT = 10

# 模拟商品数据（用于演示，当真实爬取失败时的备选方案）
SIMULATED_PRODUCTS = [
    {"name": "iPhone 13", "price": 5999.0, "sales": 1500, "category": "手机", "url": "https://example.com/iphone13"},
    {"name": "MacBook Pro", "price": 12999.0, "sales": 800, "category": "电脑", "url": "https://example.com/macbook"},
    {"name": "iPad Air", "price": 4399.0, "sales": 1200, "category": "平板", "url": "https://example.com/ipadair"},
    {"name": "AirPods Pro", "price": 1999.0, "sales": 2000, "category": "耳机", "url": "https://example.com/airpods"},
    {"name": "Samsung Galaxy S21", "price": 4999.0, "sales": 900, "category": "手机", "url": "https://example.com/s21"},
    {"name": "Dell XPS 13", "price": 8999.0, "sales": 600, "category": "电脑", "url": "https://example.com/dellxps"},
    {"name": "Surface Pro 7", "price": 7999.0, "sales": 500, "category": "平板", "url": "https://example.com/surfacepro"},
    {"name": "Sony WH-1000XM4", "price": 2899.0, "sales": 1100, "category": "耳机", "url": "https://example.com/sonyheadphones"},
    {"name": "Huawei P50", "price": 5488.0, "sales": 750, "category": "手机", "url": "https://example.com/p50"},
    {"name": "Lenovo ThinkPad X1", "price": 9999.0, "sales": 400, "category": "电脑", "url": "https://example.com/thinkpad"}
]