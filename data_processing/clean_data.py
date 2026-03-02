"""
数据清洗与嵌入生成脚本
 - 读取由爬虫输出的 JSONL 文件（默认 data/products.jsonl）
 - 清洗、规范字段
 - 将商品写入数据库（使用 database.db_utils.insert_products）
 - 使用 TF-IDF 对标题+属性构建 embedding，并写入 product_embeddings 表

用法：
  python -m data_processing.clean_data data/products.jsonl
"""
import sys
import os
import json
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import insert_products, insert_product_embedding


def read_jsonl(path: str) -> List[Dict]:
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def text_for_embedding(item: Dict) -> str:
    parts = []
    if item.get('title'):
        parts.append(item['title'])
    # attributes dict -> flat string
    attrs = item.get('attributes') or {}
    if isinstance(attrs, dict):
        parts.extend([f"{k}:{v}" for k, v in attrs.items()])
    elif isinstance(attrs, str):
        parts.append(attrs)
    # category list
    cat = item.get('category')
    if isinstance(cat, list):
        parts.extend(cat)
    elif isinstance(cat, str):
        parts.append(cat)
    return ' '.join(parts)


def build_and_store_embeddings(items: List[Dict], db_path: str = 'ecommerce.db') -> int:
    texts = [text_for_embedding(it) for it in items]
    vectorizer = TfidfVectorizer(max_features=512)
    X = vectorizer.fit_transform(texts)

    for idx, item in enumerate(items):
        pid = item.get('product_id') or item.get('url') or item.get('title')
        if pid is None:
            continue
        vec = X[idx].toarray().ravel().tolist()
        insert_product_embedding(str(pid), vec, db_path)

    return X.shape[0]


def main(jsonl_path: str = 'data/products.jsonl', db_path: str = 'ecommerce.db'):
    if not os.path.exists(jsonl_path):
        print(f"找不到文件: {jsonl_path}")
        return

    items = read_jsonl(jsonl_path)
    if not items:
        print("没有读取到商品数据")
        return

    # 简单清洗：确保字段存在并转换类型
    cleaned = []
    for it in items:
        prod = {
            'name': it.get('title') or it.get('name'),
            'price': float(it.get('price') or 0.0),
            'sales': int(it.get('sales') or 0),
            'category': it.get('category') if it.get('category') else '未知',
            'url': it.get('url'),
            'attributes': it.get('attributes'),
            'rating': it.get('rating'),
            'reviews_count': it.get('reviews_count'),
            'sku': it.get('sku'),
            'seller': it.get('seller'),
            'images': it.get('images'),
            'crawl_time': it.get('crawl_time')
        }
        cleaned.append(prod)

    # 插入数据库
    insert_products(cleaned, db_path)

    # 生成并保存embedding
    n = build_and_store_embeddings(items, db_path)
    print(f"为 {n} 个商品生成并保存了embedding")


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/products.jsonl'
    main(path)
"""
数据清洗模块
负责对爬取的商品数据进行清洗和预处理
"""
from typing import List, Dict
import re


def remove_duplicates(products: List[Dict]) -> List[Dict]:
    """
    去除重复商品
    
    Args:
        products: 原始商品列表
        
    Returns:
        去重后的商品列表
    """
    seen_names = set()
    unique_products = []
    
    for product in products:
        name = product.get('name', '')
        if name not in seen_names:
            seen_names.add(name)
            unique_products.append(product)
    
    print(f"去重完成，原始数据 {len(products)} 条，去重后 {len(unique_products)} 条")
    return unique_products


def handle_missing_values(products: List[Dict]) -> List[Dict]:
    """
    处理缺失值
    
    Args:
        products: 商品列表
        
    Returns:
        处理缺失值后的商品列表
    """
    processed_products = []
    
    for product in products:
        # 处理缺失值，为缺失的字段设置默认值
        processed_product = product.copy()
        
        # 如果没有价格，默认为0
        if 'price' not in processed_product or processed_product['price'] is None:
            processed_product['price'] = 0.0
        
        # 如果没有销量，默认为0
        if 'sales' not in processed_product or processed_product['sales'] is None:
            processed_product['sales'] = 0
        
        # 如果没有分类，默认为'未知'
        if 'category' not in processed_product or processed_product['category'] is None:
            processed_product['category'] = '未知'
        
        # 如果没有名称，默认为'未知商品'
        if 'name' not in processed_product or processed_product['name'] is None:
            processed_product['name'] = '未知商品'
        
        # 如果没有URL，默认为空字符串
        if 'url' not in processed_product or processed_product['url'] is None:
            processed_product['url'] = ''
        
        processed_products.append(processed_product)
    
    print(f"缺失值处理完成，共处理 {len(processed_products)} 条数据")
    return processed_products


def normalize_price_and_sales(products: List[Dict]) -> List[Dict]:
    """
    标准化价格和销量字段
    
    Args:
        products: 商品列表
        
    Returns:
        标准化后的商品列表
    """
    normalized_products = []
    
    for product in products:
        normalized_product = product.copy()
        
        # 标准化价格字段
        price = product['price']
        if isinstance(price, str):
            # 移除价格中的非数字字符（保留小数点）
            price = re.sub(r'[^\d.]', '', price)
            try:
                price = float(price)
            except ValueError:
                price = 0.0
        elif not isinstance(price, (int, float)):
            price = 0.0
        
        normalized_product['price'] = round(float(price), 2)
        
        # 标准化销量字段
        sales = product['sales']
        if isinstance(sales, str):
            # 移除销量中的非数字字符
            sales = re.sub(r'[^\d]', '', sales)
            try:
                sales = int(sales)
            except ValueError:
                sales = 0
        elif not isinstance(sales, int):
            sales = int(sales) if sales is not None else 0
        
        normalized_product['sales'] = int(sales)
        
        normalized_products.append(normalized_product)
    
    print(f"价格和销量标准化完成")
    return normalized_products


def clean_data(products: List[Dict]) -> List[Dict]:
    """
    执行完整的数据清洗流程
    
    Args:
        products: 原始商品数据
        
    Returns:
        清洗后的商品数据
    """
    print("开始数据清洗...")
    
    # 步骤1: 处理缺失值
    products = handle_missing_values(products)
    
    # 步骤2: 标准化价格和销量
    products = normalize_price_and_sales(products)
    
    # 步骤3: 去除重复商品
    products = remove_duplicates(products)
    
    print("数据清洗完成")
    return products