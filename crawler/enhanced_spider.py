"""
增强版爬虫模块
将爬取到的商品标准化为 JSONL，包含完整字段集，便于后续导入与分析

字段示例：
  product_id, title, category (列表), attributes (dict), price (float), rating (float), reviews_count (int), sales (int), images (list), sku, seller, crawl_time, url

用法示例：
  from crawler.enhanced_spider import crawl_and_write_jsonl
  crawl_and_write_jsonl('data/products.jsonl')
"""
from typing import List, Dict
import json
import hashlib
from datetime import datetime
import os

from .spider import crawl_all_pages


def _make_product_id(source: Dict) -> str:
    """基于URL或名称生成稳定的product_id（hex hash）"""
    key = source.get('url') or source.get('name') or ''
    return hashlib.sha1(key.encode('utf-8')).hexdigest()


def _standardize_product(raw: Dict) -> Dict:
    """将原始爬虫商品映射为标准字段结构"""
    prod = {}
    prod['product_id'] = raw.get('product_id') or _make_product_id(raw)
    prod['title'] = raw.get('name') or raw.get('title') or ''

    # category 支持 list 或 单字符串
    cat = raw.get('category')
    if isinstance(cat, list):
        prod['category'] = cat
    elif isinstance(cat, str):
        # 简单按 / 或 > 切分多级类目
        if '>' in cat:
            prod['category'] = [c.strip() for c in cat.split('>') if c.strip()]
        elif '/' in cat:
            prod['category'] = [c.strip() for c in cat.split('/') if c.strip()]
        else:
            prod['category'] = [cat]
    else:
        prod['category'] = []

    # attributes 期望为 dict
    attrs = raw.get('attributes') or {}
    if isinstance(attrs, str):
        try:
            attrs = json.loads(attrs)
        except Exception:
            attrs = { 'raw': attrs }
    prod['attributes'] = attrs

    # 基本数值字段
    try:
        prod['price'] = float(raw.get('price') or 0.0)
    except Exception:
        prod['price'] = 0.0

    prod['rating'] = raw.get('rating') if raw.get('rating') is not None else None
    prod['reviews_count'] = int(raw.get('reviews_count') or 0)
    prod['sales'] = int(raw.get('sales') or 0)

    # images 列表
    imgs = raw.get('images') or raw.get('image') or []
    if isinstance(imgs, str):
        imgs = [imgs]
    prod['images'] = imgs

    prod['sku'] = raw.get('sku')
    prod['seller'] = raw.get('seller')
    prod['url'] = raw.get('url')

    # 爬取时间
    prod['crawl_time'] = raw.get('crawl_time') or datetime.utcnow().isoformat() + 'Z'

    return prod


def crawl_and_write_jsonl(output_path: str = 'data/products.jsonl') -> int:
    """执行爬取，并将结果写入 JSONL 文件，返回写入条数"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    raw_products = crawl_all_pages()

    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for raw in raw_products:
            std = _standardize_product(raw)
            f.write(json.dumps(std, ensure_ascii=False) + '\n')
            count += 1

    print(f"爬取并写入 {count} 条商品到 {output_path}")
    return count


if __name__ == '__main__':
    crawl_and_write_jsonl()
