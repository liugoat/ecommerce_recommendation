"""
热门推荐模块
根据销量或行为次数排序，返回Top-N热门商品
"""
from typing import List, Dict
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import get_popular_products


def get_popular_recommendations(top_n: int = 10, db_path: str = "ecommerce.db") -> List[Dict]:
    """
    获取热门推荐商品
    
    Args:
        top_n: 推荐商品数量
        db_path: 数据库文件路径
        
    Returns:
        热门商品列表
    """
    # 从数据库获取按销量排序的商品
    popular_products = get_popular_products(limit=top_n, db_path=db_path)
    
    print(f"获取热门推荐商品，共 {len(popular_products)} 个")
    return popular_products


def get_new_arrivals(top_n: int = 10, db_path: str = "ecommerce.db") -> List[Dict]:
    """
    获取新品推荐（按爬取时间或上架时间降序）
    """
    conn = None
    try:
        from database.db_init import get_db_connection
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, price, sales, category, crawl_time
            FROM products
            WHERE crawl_time IS NOT NULL
            ORDER BY crawl_time DESC
            LIMIT ?
        """, (top_n,))

        rows = cursor.fetchall()
        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'sales': row[3],
                'category': row[4],
                'crawl_time': row[5]
            })

        return products
    except Exception as e:
        print(f"获取新品时出错: {e}")
        return []
    finally:
        if conn:
            conn.close()