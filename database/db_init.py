"""
数据库初始化模块
负责创建数据库表结构
"""
import sqlite3
import os


def init_database(db_path: str = "ecommerce.db"):
    """
    初始化数据库表结构
    
    Args:
        db_path: 数据库文件路径
    """
    # 连接到数据库（如果不存在则会创建）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            sales INTEGER DEFAULT 0,
            category TEXT NOT NULL,
            url TEXT,
            attributes TEXT, -- JSON string of key/value attributes
            rating REAL DEFAULT NULL,
            reviews_count INTEGER DEFAULT 0,
            sku TEXT,
            seller TEXT,
            images TEXT, -- JSON array of image URLs
            crawl_time TEXT
        )
    """)
    
    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 添加用户角色字段（兼容旧表）
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {c[1] for c in cursor.fetchall()}
    if 'role' not in user_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            print('已向 users 表添加 role 字段')
        except Exception:
            pass
    
    # 检查并添加password字段（如果不存在）
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'password' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT")
        print("已添加password字段到users表")
    
    # 确保products表包含推荐使用的扩展字段（兼容旧表）
    cursor.execute("PRAGMA table_info(products)")
    prod_columns = {column[1] for column in cursor.fetchall()}

    extra_columns = {
        'attributes': 'TEXT',
        'rating': 'REAL',
        'reviews_count': 'INTEGER',
        'sku': 'TEXT',
        'seller': 'TEXT',
        'images': 'TEXT',
        'crawl_time': 'TEXT'
    }

    for col, col_type in extra_columns.items():
        if col not in prod_columns:
            try:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {col_type}")
                print(f"已向products表添加字段: {col} {col_type}")
            except Exception as e:
                print(f"添加字段 {col} 失败: {e}")

    # 创建收藏表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # 创建产品向量表，用于内容相似度检索（embedding以JSON数组形式存储）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_embeddings (
            product_id TEXT PRIMARY KEY,
            embedding TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建评论表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER,
            rating INTEGER,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 创建产品情感汇总表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_sentiment (
            product_id INTEGER PRIMARY KEY,
            avg_sentiment REAL,
            positive_count INTEGER DEFAULT 0,
            negative_count INTEGER DEFAULT 0,
            neutral_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # 创建订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            price REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    # 创建用户行为表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_behavior (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            action TEXT NOT NULL,  -- 'view', 'click', 'buy', 'like'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    
    print(f"数据库初始化完成，数据库文件: {db_path}")


def get_db_connection(db_path: str = "ecommerce.db"):
    """
    获取数据库连接
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        数据库连接对象
    """
    return sqlite3.connect(db_path)