"""
基于用户行为的简单协同过滤（基于物品共现）
算法：统计所有用户行为中物品对的共现次数，对目标用户已交互物品的邻近物品进行加权求和
适用于数据量较小/中等的离线计算或教学演示
"""
from typing import List, Dict
import sys
import os
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import get_all_user_behaviors, query_all_products, get_user_behaviors


def recommend_by_user(user_id: int, top_n: int = 10, db_path: str = 'ecommerce.db') -> List[Dict]:
    # 获取所有用户行为
    users = get_all_user_behaviors(db_path)

    # 构建物品共现计数
    cooc = defaultdict(lambda: defaultdict(int))
    for uid, items in users.items():
        unique_items = list(dict.fromkeys(items))
        for i in range(len(unique_items)):
            for j in range(i+1, len(unique_items)):
                a = unique_items[i]
                b = unique_items[j]
                cooc[a][b] += 1
                cooc[b][a] += 1

    # 获取目标用户已交互的商品集合
    target_behaviors = get_user_behaviors(user_id, db_path)
    interacted = set([b['product_id'] for b in target_behaviors])

    # 累计候选商品得分
    scores = defaultdict(int)
    for item in interacted:
        neighbors = cooc.get(item, {})
        for nb, cnt in neighbors.items():
            if nb in interacted:
                continue
            scores[nb] += cnt

    # 按分数排序并返回商品信息
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    if not sorted_items:
        return []

    # 将product_id映射为数据库记录
    all_products = query_all_products(db_path)
    product_map = {p['id']: p for p in all_products}

    results = []
    for pid, score in sorted_items:
        p = product_map.get(pid)
        if p:
            p_copy = p.copy()
            p_copy['score'] = int(score)
            results.append(p_copy)

    return results
"""
协同过滤推荐模块
基于用户行为的协同过滤算法
"""
from typing import List, Dict
import numpy as np
import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import get_user_behaviors, query_all_products


def build_user_item_matrix(db_path: str = "ecommerce.db") -> (np.ndarray, Dict, Dict):
    """
    构建用户-商品矩阵
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        用户-商品矩阵，用户ID到索引的映射，商品ID到索引的映射
    """
    # 获取所有用户行为记录
    # 注意：这里需要扩展数据库查询以获取用户行为数据
    # 由于我们没有直接的查询函数，需要创建一个
    
    conn = __import__('sqlite3').connect(db_path)
    cursor = conn.cursor()
    
    # 查询用户行为数据
    cursor.execute("""
        SELECT user_id, product_id, action
        FROM user_behavior
        ORDER BY user_id, product_id
    """)
    
    behaviors = cursor.fetchall()
    conn.close()
    
    # 获取所有用户和商品ID
    user_ids = list(set([row[0] for row in behaviors]))
    product_ids = list(set([row[1] for row in behaviors]))
    
    # 创建ID到索引的映射
    user_id_to_idx = {user_id: idx for idx, user_id in enumerate(user_ids)}
    product_id_to_idx = {product_id: idx for idx, product_id in enumerate(product_ids)}
    
    # 初始化用户-商品矩阵
    user_item_matrix = np.zeros((len(user_ids), len(product_ids)))
    
    # 填充矩阵，这里简单地将行为视为评分
    for user_id, product_id, action in behaviors:
        user_idx = user_id_to_idx[user_id]
        product_idx = product_id_to_idx[product_id]
        
        # 根据行为类型给予不同评分
        if action == 'view':
            rating = 1
        elif action == 'click':
            rating = 2
        elif action == 'like':
            rating = 3
        elif action == 'buy':
            rating = 5
        else:
            rating = 1
            
        user_item_matrix[user_idx][product_idx] += rating
    
    return user_item_matrix, user_id_to_idx, product_id_to_idx


def compute_user_similarity(user_item_matrix: np.ndarray) -> np.ndarray:
    """
    计算用户之间的相似度矩阵
    
    Args:
        user_item_matrix: 用户-商品矩阵
        
    Returns:
        用户相似度矩阵
    """
    # 使用余弦相似度计算用户相似度
    from sklearn.metrics.pairwise import cosine_similarity
    similarity_matrix = cosine_similarity(user_item_matrix)
    return similarity_matrix


def recommend_by_user(
    user_id: int, 
    top_n: int = 5, 
    db_path: str = "ecommerce.db"
) -> List[Dict]:
    """
    为指定用户推荐商品（基于协同过滤）
    
    Args:
        user_id: 用户ID
        top_n: 推荐数量
        db_path: 数据库文件路径
        
    Returns:
        推荐商品列表
    """
    # 构建用户-商品矩阵
    user_item_matrix, user_id_to_idx, product_id_to_idx = build_user_item_matrix(db_path)
    
    # 检查用户是否在矩阵中
    if user_id not in user_id_to_idx:
        print(f"用户 {user_id} 没有足够的行为数据，无法使用协同过滤推荐")
        return []
    
    current_user_idx = user_id_to_idx[user_id]
    
    # 计算用户相似度
    similarity_matrix = compute_user_similarity(user_item_matrix)
    
    # 获取与当前用户最相似的其他用户
    user_similarities = similarity_matrix[current_user_idx]
    similar_user_indices = np.argsort(user_similarities)[::-1][1:]  # 排除自身
    
    # 获取当前用户已购买的商品
    user_behaviors = get_user_behaviors(user_id, db_path)
    purchased_product_ids = [behavior['product_id'] for behavior in user_behaviors]
    
    # 获取所有商品信息
    all_products = query_all_products(db_path)
    product_idx_to_id = {v: k for k, v in product_id_to_idx.items()}
    
    # 为当前用户推荐商品
    product_scores = {}
    
    for similar_user_idx in similar_user_indices[:10]:  # 只考虑前10个相似用户
        similarity = user_similarities[similar_user_idx]
        
        # 获取相似用户评分较高的商品
        for product_idx, rating in enumerate(user_item_matrix[similar_user_idx]):
            if rating > 0:  # 相似用户对商品有行为
                product_id = product_idx_to_id[product_idx]
                
                # 如果当前用户未与该商品交互过，则考虑推荐
                if product_id not in purchased_product_ids:
                    if product_id not in product_scores:
                        product_scores[product_id] = 0
                    # 根据相似度和评分计算推荐分数
                    product_scores[product_id] += similarity * rating
    
    # 按分数排序并获取推荐商品
    sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    recommendations = []
    for product_id, score in sorted_products:
        product = next((p for p in all_products if p['id'] == product_id), None)
        if product:
            product['score'] = score
            recommendations.append(product)
    
    print(f"为用户 {user_id} 基于协同过滤推荐 {len(recommendations)} 个商品")
    return recommendations