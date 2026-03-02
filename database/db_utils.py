"""
数据库工具模块
提供对数据库的增删改查操作
"""
from typing import List, Dict, Optional
import sqlite3
import hashlib
import json
from .db_init import get_db_connection


def insert_products(products: List[Dict], db_path: str = "ecommerce.db"):
    """
    批量插入商品数据
    
    Args:
        products: 商品数据列表
        db_path: 数据库文件路径
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # 批量插入商品数据，扩展字段兼容
    for product in products:
        # 基本类型化与兼容性处理，避免向sqlite绑定不支持的类型
        name = product.get('name') or product.get('title') or ''
        try:
            price = float(product.get('price') or 0.0)
        except Exception:
            price = 0.0
        try:
            sales = int(product.get('sales') or 0)
        except Exception:
            sales = 0

        # category 可能为 list 或 str
        category = product.get('category')
        if isinstance(category, (list, dict)):
            try:
                category = json.dumps(category, ensure_ascii=False)
            except Exception:
                category = str(category)
        elif category is None:
            category = ''
        else:
            category = str(category)

        url = product.get('url')

        attributes = product.get('attributes')
        if attributes is not None and not isinstance(attributes, str):
            try:
                attributes = json.dumps(attributes, ensure_ascii=False)
            except Exception:
                attributes = str(attributes)

        try:
            rating = float(product.get('rating')) if product.get('rating') is not None else None
        except Exception:
            rating = None

        try:
            reviews_count = int(product.get('reviews_count') or 0)
        except Exception:
            reviews_count = 0

        sku = product.get('sku')
        seller = product.get('seller')

        images = product.get('images')
        if images is not None and not isinstance(images, str):
            try:
                images = json.dumps(images, ensure_ascii=False)
            except Exception:
                images = str(images)

        crawl_time = product.get('crawl_time')

        cursor.execute("""
            INSERT OR IGNORE INTO products (name, price, sales, category, url, attributes, rating, reviews_count, sku, seller, images, crawl_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            price,
            sales,
            category,
            url,
            attributes,
            rating,
            reviews_count,
            sku,
            seller,
            images,
            crawl_time
        ))
    
    conn.commit()
    conn.close()
    
    try:
        print(f"??????? {len(products)} ???")
    except OSError:
        # Avoid request failure when stdout is invalid in some environments.
        pass


def insert_user(username: str, db_path: str = "ecommerce.db") -> int:
    """
    插入用户（如果用户不存在则创建）
    
    Args:
        username: 用户名
        db_path: 数据库文件路径
        
    Returns:
        用户ID
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        # 先检查用户是否已存在
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            # 用户已存在，返回其ID
            user_id = result[0]
            print(f"用户 '{username}' 已存在，ID: {user_id}")
            return user_id
        else:
            # 用户不存在，插入新用户，password设为NULL（因为这是模拟用户）
            cursor.execute("INSERT INTO users (username, password) VALUES (?, NULL)", (username,))
            conn.commit()
            
            # 获取新插入用户的ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                print(f"用户 '{username}' 创建成功，ID: {user_id}")
                return user_id
            else:
                print(f"插入用户失败: {username}")
                return -1
    except Exception as e:
        print(f"插入用户时出错: {e}")
        return -1
    finally:
        conn.close()


def query_all_products(db_path: str = "ecommerce.db") -> List[Dict]:
    """
    查询所有商品
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        商品数据列表
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.name, p.price, p.sales, p.category, p.url, p.attributes, p.rating, p.reviews_count, p.sku, p.seller, p.images, p.crawl_time,
               ps.avg_sentiment, ps.positive_count, ps.negative_count, ps.neutral_count
        FROM products p
        LEFT JOIN product_sentiment ps ON ps.product_id = p.id
    """)
    rows = cursor.fetchall()
    
    products = []
    for row in rows:
        product = {
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'sales': row[3],
            'category': row[4],
            'url': row[5],
            'attributes': None,
            'rating': None,
            'reviews_count': 0,
            'sku': None,
            'seller': None,
            'images': None,
            'crawl_time': None
        }
        # 解析可选扩展字段（索引对应于SELECT顺序）
        try:
            product['attributes'] = json.loads(row[6]) if row[6] else None
        except Exception:
            product['attributes'] = row[6]

        product['rating'] = row[7]
        product['reviews_count'] = row[8]
        product['sku'] = row[9]
        product['seller'] = row[10]
        try:
            product['images'] = json.loads(row[11]) if row[11] else None
        except Exception:
            product['images'] = row[11]

        product['crawl_time'] = row[12]
        # sentiment fields
        product['avg_sentiment'] = row[13]
        product['positive_count'] = row[14]
        product['negative_count'] = row[15]
        product['neutral_count'] = row[16]
        products.append(product)
    
    conn.close()
    
    try:
        print(f"从数据库查询到 {len(products)} 个商品")
    except OSError:
        # Avoid request failure when stdout is invalid in some environments.
        pass
    return products


def register_user(username: str, password: str, db_path: str = "ecommerce.db") -> int:
    """
    注册用户
    
    Args:
        username: 用户名
        password: 密码
        db_path: 数据库文件路径
        
    Returns:
        用户ID
    """
    # 对密码进行哈希处理
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        user_id = cursor.lastrowid
        conn.commit()
        print(f"用户 '{username}' 注册成功，ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError:
        # 如果用户名已存在
        print(f"用户名 '{username}' 已存在")
        return -1
    finally:
        conn.close()


def get_user_by_username(username: str, db_path: str = "ecommerce.db") -> Optional[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {'id': row[0], 'username': row[1], 'role': row[2], 'created_at': row[3]}


def set_user_role(user_id: int, role: str = 'user', db_path: str = 'ecommerce.db') -> bool:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    ok = cursor.rowcount > 0
    conn.close()
    return ok


def login_user(username: str, password: str, db_path: str = "ecommerce.db") -> int:
    """
    用户登录
    
    Args:
        username: 用户名
        password: 密码
        db_path: 数据库文件路径
        
    Returns:
        用户ID，如果登录失败返回-1
    """
    # 对输入的密码进行哈希处理
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    else:
        print(f"用户名或密码错误")
        return -1


def insert_user_behavior(user_id: int, product_id: int, action: str, db_path: str = "ecommerce.db"):
    """
    插入用户行为记录
    
    Args:
        user_id: 用户ID
        product_id: 商品ID
        action: 行为类型 ('view', 'click', 'buy', 'like')
        db_path: 数据库文件路径
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO user_behavior (user_id, product_id, action)
        VALUES (?, ?, ?)
    """, (user_id, product_id, action))
    
    conn.commit()
    conn.close()
    
    print(f"用户行为记录插入成功: 用户{user_id}, 商品{product_id}, 行为{action}")


def get_user_behaviors(user_id: int, db_path: str = "ecommerce.db") -> List[Dict]:
    """
    获取用户行为记录
    
    Args:
        user_id: 用户ID
        db_path: 数据库文件路径
        
    Returns:
        用户行为记录列表
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ub.product_id, ub.action, ub.timestamp
        FROM user_behavior ub
        WHERE ub.user_id = ?
        ORDER BY ub.timestamp DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    
    behaviors = []
    for row in rows:
        behavior = {
            'product_id': row[0],
            'action': row[1],
            'timestamp': row[2]
        }
        behaviors.append(behavior)
    
    conn.close()
    
    return behaviors


def get_popular_products(limit: int = 10, db_path: str = "ecommerce.db") -> List[Dict]:
    """
    获取热门商品（根据销量排序）
    
    Args:
        limit: 返回商品数量限制
        db_path: 数据库文件路径
        
    Returns:
        热门商品列表
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, price, sales, category
        FROM products
        ORDER BY sales DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    
    products = []
    for row in rows:
        product = {
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'sales': row[3],
            'category': row[4]
        }
        products.append(product)
    
    conn.close()
    
    return products


def insert_product_embedding(product_id: str, embedding: List[float], db_path: str = "ecommerce.db"):
    """插入或更新商品embedding（JSON格式）"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    emb_json = json.dumps(embedding)
    cursor.execute("""
        INSERT INTO product_embeddings (product_id, embedding, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(product_id) DO UPDATE SET embedding=excluded.embedding, updated_at=CURRENT_TIMESTAMP
    """, (product_id, emb_json))
    conn.commit()
    conn.close()


def query_product_embedding(product_id: str, db_path: str = "ecommerce.db") -> Optional[List[float]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT embedding FROM product_embeddings WHERE product_id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def query_all_embeddings(db_path: str = "ecommerce.db") -> Dict[str, List[float]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, embedding FROM product_embeddings")
    rows = cursor.fetchall()
    conn.close()
    result = {}
    for pid, emb in rows:
        try:
            result[pid] = json.loads(emb) if emb else None
        except Exception:
            result[pid] = None
    return result


### Product CRUD helpers
def get_product_by_id(product_id: int, db_path: str = 'ecommerce.db') -> Optional[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, sales, category, url FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {'id': row[0], 'name': row[1], 'price': row[2], 'sales': row[3], 'category': row[4], 'url': row[5]}


def create_product(data: Dict, db_path: str = 'ecommerce.db') -> int:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price, sales, category, url) VALUES (?, ?, ?, ?, ?)", (
        data.get('name'), data.get('price') or 0.0, data.get('sales') or 0, data.get('category') or '', data.get('url') or ''
    ))
    conn.commit()
    pid = cursor.lastrowid
    conn.close()
    return pid


def update_product(product_id: int, data: Dict, db_path: str = 'ecommerce.db') -> bool:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products SET name = ?, price = ?, sales = ?, category = ?, url = ? WHERE id = ?
    """, (data.get('name'), data.get('price') or 0.0, data.get('sales') or 0, data.get('category') or '', data.get('url') or '', product_id))
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed


def delete_product(product_id: int, db_path: str = 'ecommerce.db') -> bool:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


### Orders helpers
def create_order(user_id: int, product_id: int, quantity: int, price: float, db_path: str = 'ecommerce.db') -> int:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, product_id, quantity, price, status) VALUES (?, ?, ?, ?, 'pending')", (user_id, product_id, quantity, price))
    conn.commit()
    oid = cursor.lastrowid
    conn.close()
    return oid


def get_orders(limit: int = 100, db_path: str = 'ecommerce.db') -> List[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, product_id, quantity, price, status, created_at FROM orders ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'user_id': r[1], 'product_id': r[2], 'quantity': r[3], 'price': r[4], 'status': r[5], 'created_at': r[6]} for r in rows]


def update_order_status(order_id: int, status: str, db_path: str = 'ecommerce.db') -> bool:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    ok = cursor.rowcount > 0
    conn.close()
    return ok


def export_orders_csv(path: str = 'orders_export.csv', db_path: str = 'ecommerce.db') -> str:
    import csv
    orders = get_orders(10000, db_path)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'user_id', 'product_id', 'quantity', 'price', 'status', 'created_at'])
        for o in orders:
            writer.writerow([o['id'], o['user_id'], o['product_id'], o['quantity'], o['price'], o['status'], o['created_at']])
    return path


def insert_favorite(user_id: int, product_id: int, db_path: str = "ecommerce.db"):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO favorites (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
    conn.commit()
    conn.close()


def remove_favorite(user_id: int, product_id: int, db_path: str = "ecommerce.db"):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    conn.commit()
    conn.close()


def get_user_favorites(user_id: int, db_path: str = "ecommerce.db") -> List[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.price, p.sales, p.category, p.url
        FROM products p
        JOIN favorites f ON f.product_id = p.id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    favs = []
    for row in rows:
        favs.append({'id': row[0], 'name': row[1], 'price': row[2], 'sales': row[3], 'category': row[4], 'url': row[5]})
    return favs


def get_all_user_behaviors(db_path: str = "ecommerce.db") -> Dict[int, List[int]]:
    """返回字典：user_id -> 列表的 product_id（按时间）"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, product_id FROM user_behavior ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close()
    users = {}
    for user_id, product_id in rows:
        users.setdefault(user_id, []).append(product_id)
    return users


def get_all_users(db_path: str = 'ecommerce.db') -> List[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'username': r[1], 'role': r[2], 'created_at': r[3]} for r in rows]


def insert_review(product_id: int, user_id: int, rating: int, content: str, db_path: str = 'ecommerce.db') -> int:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reviews (product_id, user_id, rating, content) VALUES (?, ?, ?, ?)", (product_id, user_id, rating, content))
    conn.commit()
    rid = cursor.lastrowid
    conn.close()
    return rid


def query_reviews_by_product(product_id: int, db_path: str = 'ecommerce.db') -> List[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, rating, content, created_at FROM reviews WHERE product_id = ? ORDER BY created_at DESC", (product_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'user_id': r[1], 'rating': r[2], 'content': r[3], 'created_at': r[4]} for r in rows]


def upsert_product_sentiment(product_id: int, avg_sentiment: float, pos: int, neg: int, neu: int, db_path: str = 'ecommerce.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO product_sentiment (product_id, avg_sentiment, positive_count, negative_count, neutral_count, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(product_id) DO UPDATE SET avg_sentiment=excluded.avg_sentiment, positive_count=excluded.positive_count, negative_count=excluded.negative_count, neutral_count=excluded.neutral_count, updated_at=CURRENT_TIMESTAMP
    """, (product_id, avg_sentiment, pos, neg, neu))
    conn.commit()
    conn.close()


def query_product_sentiment(product_id: int, db_path: str = 'ecommerce.db') -> Optional[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT avg_sentiment, positive_count, negative_count, neutral_count, updated_at FROM product_sentiment WHERE product_id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {'avg_sentiment': row[0], 'positive_count': row[1], 'negative_count': row[2], 'neutral_count': row[3], 'updated_at': row[4]}


def aggregate_all_product_sentiments(db_path: str = 'ecommerce.db') -> List[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, avg_sentiment, positive_count, negative_count, neutral_count FROM product_sentiment")
    rows = cursor.fetchall()
    conn.close()
    return [{'product_id': r[0], 'avg_sentiment': r[1], 'positive_count': r[2], 'negative_count': r[3], 'neutral_count': r[4]} for r in rows]


def get_recent_behaviors(limit: int = 200, db_path: str = 'ecommerce.db') -> List[Dict]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ub.id, ub.user_id, u.username, ub.product_id, p.name, ub.action, ub.timestamp
        FROM user_behavior ub
        LEFT JOIN users u ON u.id = ub.user_id
        LEFT JOIN products p ON p.id = ub.product_id
        ORDER BY ub.timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'user_id': r[1], 'username': r[2], 'product_id': r[3], 'product_name': r[4], 'action': r[5], 'timestamp': r[6]} for r in rows]
