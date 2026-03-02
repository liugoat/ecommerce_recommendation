"""
基于内容的相似商品推荐
使用存储在 `product_embeddings` 表中的 embedding，基于余弦相似度返回相似商品
"""
from typing import List, Dict, Optional
import math
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import query_all_embeddings, query_all_products, query_product_embedding


def _cosine(a: List[float], b: List[float]) -> float:
    a = np.array(a)
    b = np.array(b)
    if a.size == 0 or b.size == 0:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def recommend_similar_products(product_id: int, feature_matrix=None, top_n: int = 10, db_path: str = 'ecommerce.db') -> List[Dict]:
    """
    返回与指定商品相似的商品列表。
    product_id: 数据库中的整数id
    如果找不到对应embedding，则返回空列表
    """
    # 获取所有商品以便通过db id查找url/name
    all_products = query_all_products(db_path)
    target = next((p for p in all_products if p['id'] == product_id), None)
    if not target:
        print(f"找不到商品 id={product_id}")
        return []

    # 尝试使用多种key去查找embedding：url、name、str(id)
    keys_to_try = []
    if target.get('url'):
        keys_to_try.append(target['url'])
    if target.get('name'):
        keys_to_try.append(target['name'])
    keys_to_try.append(str(product_id))

    embeddings = query_all_embeddings(db_path)
    target_emb = None
    target_key = None
    for k in keys_to_try:
        if k in embeddings and embeddings[k] is not None:
            target_emb = embeddings[k]
            target_key = k
            break

    if target_emb is None:
        print(f"未找到商品的embedding (尝试键: {keys_to_try})")
        return []

    # 计算相似度
    scores = []
    for k, emb in embeddings.items():
        if emb is None or k == target_key:
            continue
        sim = _cosine(target_emb, emb)
        scores.append((k, sim))

    scores.sort(key=lambda x: x[1], reverse=True)

    # 将前top_n的embedding key映射回数据库商品（通过url或name或id匹配）
    results = []
    for key, score in scores[:top_n]:
        # 尝试匹配数据库商品
        match = None
        for p in all_products:
            if p.get('url') == key or p.get('name') == key or str(p.get('id')) == key:
                match = p
                break
        if match:
            match_copy = match.copy()
            match_copy['score'] = float(score)
            results.append(match_copy)

    return results
"""
基于内容的推荐模块
使用商品特征计算相似度，推荐相似商品
"""
from typing import List, Dict
import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.metrics.pairwise import cosine_similarity
from database.db_utils import query_all_products


def compute_cosine_similarity(feature_matrix: np.ndarray) -> np.ndarray:
    """
    计算商品之间的余弦相似度矩阵
    
    Args:
        feature_matrix: 商品特征矩阵
        
    Returns:
        相似度矩阵
    """
    # 计算余弦相似度
    similarity_matrix = cosine_similarity(feature_matrix)
    return similarity_matrix


def recommend_similar_products(
    product_id: int, 
    feature_matrix: np.ndarray, 
    top_n: int = 5, 
    db_path: str = "ecommerce.db"
) -> List[Dict]:
    """
    为指定商品推荐相似商品
    
    Args:
        product_id: 目标商品ID
        feature_matrix: 商品特征矩阵
        top_n: 推荐数量
        db_path: 数据库文件路径
        
    Returns:
        相似商品列表
    """
    # 获取所有商品
    all_products = query_all_products(db_path)
    
    # 找到目标商品在列表中的索引
    target_idx = None
    for idx, product in enumerate(all_products):
        if product['id'] == product_id:
            target_idx = idx
            break
    
    if target_idx is None:
        print(f"未找到ID为 {product_id} 的商品")
        return []
    
    # 计算目标商品与其他商品的相似度
    target_features = feature_matrix[target_idx].reshape(1, -1)
    similarities = cosine_similarity(target_features, feature_matrix).flatten()
    
    # 获取最相似的商品索引（排除自身）
    similar_indices = similarities.argsort()[::-1][1:top_n+1]
    
    # 构建推荐结果
    recommendations = []
    for idx in similar_indices:
        product = all_products[idx]
        product['similarity'] = float(similarities[idx])
        recommendations.append(product)
    
    print(f"为商品 {product_id} 推荐 {len(recommendations)} 个相似商品")
    return recommendations