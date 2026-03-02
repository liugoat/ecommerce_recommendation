"""
系统主流程
执行顺序：
1. 启动爬虫，采集商品数据
2. 对原始数据进行清洗
3. 数据入库
4. 初始化模拟用户
5. 模拟用户浏览行为
6. 执行推荐算法
7. 打印推荐结果
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler.spider import crawl_all_pages
from data_processing.clean_data import clean_data
from database.db_init import init_database
from database.db_utils import insert_products, insert_user, insert_user_behavior, query_all_products
from recommendation.recommender import get_recommendations


def main():
    print("=" * 50)
    print("基于爬虫的电商购物推荐平台")
    print("=" * 50)
    
    # 步骤1: 启动爬虫，采集商品数据
    print("\n【步骤1】启动爬虫，采集商品数据...")
    raw_products = crawl_all_pages()
    print(f"爬取到 {len(raw_products)} 个原始商品数据")
    
    # 步骤2: 对原始数据进行清洗
    print("\n【步骤2】对原始数据进行清洗...")
    cleaned_products = clean_data(raw_products)
    print(f"清洗后剩余 {len(cleaned_products)} 个商品数据")
    
    # 步骤3: 数据入库
    print("\n【步骤3】数据入库...")
    db_path = "ecommerce.db"
    init_database(db_path)  # 确保数据库初始化
    
    # 在插入新数据前清空已有商品数据
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()
    print("已清空旧商品数据")
    
    insert_products(cleaned_products, db_path)
    
    # 验证数据入库
    all_products = query_all_products(db_path)
    print(f"成功入库 {len(all_products)} 个商品")
    
    # 步骤4: 初始化模拟用户
    print("\n【步骤4】初始化模拟用户...")
    user1_id = insert_user("张三", db_path)
    user2_id = insert_user("李四", db_path)
    user3_id = insert_user("王五", db_path)
    print(f"创建了3个模拟用户: ID {user1_id}, {user2_id}, {user3_id}")
    
    # 步骤5: 模拟用户浏览行为
    print("\n【步骤5】模拟用户浏览行为...")
    
    # 为用户1添加行为记录
    for i in range(0, min(5, len(all_products))):
        product_id = all_products[i]['id']
        insert_user_behavior(user1_id, product_id, 'view', db_path)
        if i % 2 == 0:
            insert_user_behavior(user1_id, product_id, 'click', db_path)
        if i == 0:
            insert_user_behavior(user1_id, product_id, 'buy', db_path)
    
    # 为用户2添加行为记录
    for i in range(3, min(8, len(all_products))):
        product_id = all_products[i]['id']
        insert_user_behavior(user2_id, product_id, 'view', db_path)
        if i % 2 == 1:
            insert_user_behavior(user2_id, product_id, 'like', db_path)
    
    # 为用户3不添加行为记录（新用户）
    print("模拟用户行为记录添加完成")
    
    # 步骤6 & 7: 执行推荐算法并打印推荐结果
    print("\n【步骤6&7】执行推荐算法并展示结果...")
    
    # 为有行为记录的用户推荐
    print(f"\n--- 为用户{user1_id}(张三)的推荐结果 ---")
    user1_recs = get_recommendations(user1_id, top_n=5, db_path=db_path)
    if user1_recs:
        for i, product in enumerate(user1_recs, 1):
            print(f"{i}. {product['name']} - ¥{product['price']} (销量: {product['sales']})")
    else:
        print("未找到推荐商品")
    
    print(f"\n--- 为用户{user2_id}(李四)的推荐结果 ---")
    user2_recs = get_recommendations(user2_id, top_n=5, db_path=db_path)
    if user2_recs:
        for i, product in enumerate(user2_recs, 1):
            print(f"{i}. {product['name']} - ¥{product['price']} (销量: {product['sales']})")
    else:
        print("未找到推荐商品")
    
    print(f"\n--- 为新用户{user3_id}(王五)的推荐结果 ---")
    user3_recs = get_recommendations(user3_id, top_n=5, db_path=db_path)
    if user3_recs:
        for i, product in enumerate(user3_recs, 1):
            print(f"{i}. {product['name']} - ¥{product['price']} (销量: {product['sales']})")
    else:
        print("未找到推荐商品")
    
    # 基于内容的推荐示例
    if all_products:
        sample_product_id = all_products[0]['id']
        print(f"\n--- 为商品ID {sample_product_id} 的相似商品推荐 ---")
        content_recs = get_recommendations(product_id=sample_product_id, top_n=5, db_path=db_path)
        if content_recs:
            for i, product in enumerate(content_recs, 1):
                print(f"{i}. {product['name']} - ¥{product['price']} (相似度: {product.get('similarity', 'N/A'):.3f})")
        else:
            print("未找到相似商品")
    
    print("\n" + "=" * 50)
    print("推荐系统运行完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()