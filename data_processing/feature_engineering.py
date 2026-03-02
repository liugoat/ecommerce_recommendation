"""
特征工程模块
负责构建商品特征矩阵，为推荐算法提供数据支持
"""
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
from collections import defaultdict


def encode_category(products: List[Dict]) -> Tuple[List[Dict], np.ndarray]:
    """
    对商品类别进行One-Hot编码
    
    Args:
        products: 商品列表
        
    Returns:
        编码后的商品列表和类别特征矩阵
    """
    # 获取所有唯一类别
    categories = set()
    for product in products:
        categories.add(product.get('category', '未知'))
    
    # 创建类别到索引的映射
    category_to_idx = {cat: idx for idx, cat in enumerate(sorted(categories))}
    
    # 创建One-Hot编码矩阵
    category_features = np.zeros((len(products), len(categories)))
    
    for idx, product in enumerate(products):
        cat = product.get('category', '未知')
        cat_idx = category_to_idx[cat]
        category_features[idx][cat_idx] = 1
    
    print(f"类别编码完成，共 {len(categories)} 个类别")
    return products, category_features


def build_feature_matrix(products: List[Dict]) -> Tuple[np.ndarray, List[str]]:
    """
    构建商品特征矩阵
    
    Args:
        products: 商品列表
        
    Returns:
        特征矩阵和特征名称列表
    """
    if not products:
        return np.array([]), []
    
    # 提取数值特征
    prices = np.array([product['price'] for product in products])
    sales = np.array([product['sales'] for product in products])
    
    # 对价格和销量进行归一化处理
    # 避免除以0的情况
    price_normalized = (prices - prices.min()) / (prices.max() - prices.min() + 1e-8)
    sales_normalized = (sales - sales.min()) / (sales.max() - sales.min() + 1e-8)
    
    # 合并数值特征
    numerical_features = np.column_stack((price_normalized, sales_normalized))
    
    # 对类别进行One-Hot编码
    _, category_features = encode_category(products)
    
    # 合并所有特征
    feature_matrix = np.hstack((numerical_features, category_features))
    
    # 构建特征名称
    feature_names = ['price_normalized', 'sales_normalized']
    
    # 添加类别特征名称
    categories = set()
    for product in products:
        categories.add(product.get('category', '未知'))
    
    for cat in sorted(categories):
        feature_names.append(f'category_{cat}')
    
    print(f"特征矩阵构建完成，形状: {feature_matrix.shape}")
    return feature_matrix, feature_names


def normalize_features(feature_matrix: np.ndarray) -> np.ndarray:
    """
    对特征矩阵进行归一化
    
    Args:
        feature_matrix: 原始特征矩阵
        
    Returns:
        归一化后的特征矩阵
    """
    # 对每一列进行归一化
    feature_min = feature_matrix.min(axis=0)
    feature_max = feature_matrix.max(axis=0)
    
    # 避免除以0的情况
    range_vals = feature_max - feature_min
    range_vals[range_vals == 0] = 1  # 如果最大值等于最小值，则设为1
    
    normalized_matrix = (feature_matrix - feature_min) / range_vals
    
    return normalized_matrix