"""
HTML解析模块
负责从HTML内容中解析出商品信息
"""
from typing import List, Dict, Optional
import sys
import os
import re

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup


def parse_product_list(html: str) -> List[Dict]:
    """
    从HTML中解析商品列表（适配books.toscrape.com网站）
    
    Args:
        html: HTML内容
        
    Returns:
        商品信息列表
    """
    products = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # books.toscrape.com网站的书籍商品在article.product_pod元素中
        product_elements = soup.find_all('article', class_='product_pod')
        
        for element in product_elements:
            product = extract_book_fields_from_element(element)
            if product and any(product.values()):  # 确保不是空数据
                products.append(product)
        
        print(f"解析到 {len(products)} 个商品")
        
    except Exception as e:
        print(f"解析HTML时出错: {e}")
    
    return products


def extract_book_fields_from_element(element) -> Dict:
    """
    从书籍元素中提取书籍字段信息（适配books.toscrape.com网站）
    
    Args:
        element: 书籍HTML元素
        
    Returns:
        包含书籍字段的字典
    """
    product = {
        'name': '',
        'price': 0.0,
        'sales': 0,  # 书籍网站没有销量信息，使用默认值
        'category': '图书',  # 默认分类为图书
        'url': ''
    }
    
    try:
        # 提取书名 - 在h3 > a > title属性或a标签的title属性中
        title_elem = element.find('h3')
        if title_elem:
            a_elem = title_elem.find('a')
            if a_elem and a_elem.get('title'):
                product['name'] = a_elem['title']
        
        # 如果没有通过h3找到，尝试其他方式
        if not product['name']:
            a_elem = element.find('a', title=True)
            if a_elem:
                product['name'] = a_elem['title']
        
        # 提取价格 - 在.price_color元素中
        price_elem = element.find('p', class_='price_color')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # 价格格式为£20.40，提取数字部分
            price_match = re.search(r'[\d.]+', price_text)
            if price_match:
                try:
                    product['price'] = float(price_match.group())
                except ValueError:
                    pass
        
        # 提取星级 - 在star-rating元素中，虽然不是价格或销量，但可以作为评价指标
        rating_elem = element.find('p', class_=re.compile(r'star-rating'))
        if rating_elem:
            rating_class = [cls for cls in rating_elem.get('class', []) if cls != 'star-rating']
            if rating_class:
                # 将星级作为销售参考（仅作为示例）
                rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
                if rating_class[0] in rating_map:
                    product['sales'] = rating_map[rating_class[0]] * 100  # 映射为虚拟销量
        
        # 提取商品链接
        link_elem = element.find('h3').find('a') if element.find('h3') else element.find('a', href=True)
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            if href.startswith('http'):
                product['url'] = href
            elif href.startswith('../'):
                # 处理相对路径
                product['url'] = f"https://books.toscrape.com/{href.replace('../', '')}"
            elif href.startswith('/'):
                product['url'] = f"https://books.toscrape.com{href}"
            else:
                product['url'] = f"https://books.toscrape.com/{href}"
        
    except Exception as e:
        print(f"提取书籍字段时出错: {e}")
    
    return product


def extract_product_fields(html: str) -> List[Dict]:
    """
    从HTML中提取商品字段信息（保留原接口）
    
    Args:
        html: HTML内容
        
    Returns:
        包含商品字段的字典列表
    """
    return parse_product_list(html)