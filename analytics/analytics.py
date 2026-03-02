"""
Analytics helper functions for dashboard APIs.
Provides sales trend, top N products, revenue by category, and simple review sentiment stub.
"""
from typing import List, Dict, Any
import sqlite3
import os
from collections import defaultdict
import json


def _get_conn(db_path: str = 'ecommerce.db'):
    return sqlite3.connect(db_path)


def sales_trend(days: int = 30, db_path: str = 'ecommerce.db') -> List[Dict[str, Any]]:
    conn = _get_conn(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y-%m-%d', timestamp) as day, COUNT(*) as buys
        FROM user_behavior
        WHERE action = 'buy' AND timestamp >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
    """, (f'-{days} days',))
    rows = cursor.fetchall()
    conn.close()
    return [{'day': r[0], 'buys': r[1]} for r in rows]


def top_n_products(n: int = 10, db_path: str = 'ecommerce.db') -> List[Dict[str, Any]]:
    conn = _get_conn(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ub.product_id, COUNT(*) as cnt, p.name, p.price
        FROM user_behavior ub
        JOIN products p ON p.id = ub.product_id
        WHERE ub.action = 'buy'
        GROUP BY ub.product_id
        ORDER BY cnt DESC
        LIMIT ?
    """, (n,))
    rows = cursor.fetchall()
    conn.close()
    return [{'product_id': r[0], 'buys': r[1], 'name': r[2], 'price': r[3]} for r in rows]


def revenue_by_category(db_path: str = 'ecommerce.db') -> List[Dict[str, Any]]:
    conn = _get_conn(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.category, COUNT(*) as buys, SUM(p.price) as revenue
        FROM user_behavior ub
        JOIN products p ON p.id = ub.product_id
        WHERE ub.action = 'buy'
        GROUP BY p.category
        ORDER BY revenue DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    merged = defaultdict(lambda: {'buys': 0, 'revenue': 0.0})

    def split_categories(raw):
        if raw is None:
            return ['未分类']
        if isinstance(raw, str):
            s = raw.strip()
            if not s:
                return ['未分类']
            if s.startswith('['):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list):
                        out = [str(x).strip() for x in arr if str(x).strip()]
                        if out:
                            return out
                except Exception:
                    pass
            for sep in ['|', '/', ',', ';']:
                if sep in s:
                    out = [x.strip() for x in s.split(sep) if x.strip()]
                    if out:
                        return out
            return [s]
        return [str(raw)]

    for category, buys, revenue in rows:
        cats = split_categories(category)
        share = (revenue or 0.0) / max(len(cats), 1)
        for c in cats:
            merged[c]['buys'] += buys or 0
            merged[c]['revenue'] += share

    result = [
        {'category': c, 'buys': v['buys'], 'revenue': round(v['revenue'], 2)}
        for c, v in merged.items()
    ]
    result.sort(key=lambda x: x['revenue'], reverse=True)
    return result


def price_distribution(category: str = None, db_path: str = 'ecommerce.db') -> Dict[str, int]:
    conn = _get_conn(db_path)
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT price FROM products WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT price FROM products")
    rows = cursor.fetchall()
    conn.close()
    buckets = defaultdict(int)
    for (price,) in rows:
        try:
            p = float(price or 0)
        except Exception:
            p = 0.0
        if p < 50:
            buckets['<50'] += 1
        elif p < 200:
            buckets['50-200'] += 1
        elif p < 1000:
            buckets['200-1000'] += 1
        else:
            buckets['1000+'] += 1
    return dict(buckets)


def review_sentiment_overview(db_path: str = 'ecommerce.db') -> Dict[str, Any]:
    from database.db_utils import aggregate_all_product_sentiments
    rows = aggregate_all_product_sentiments(db_path)
    total_pos = sum(r.get('positive_count',0) for r in rows)
    total_neg = sum(r.get('negative_count',0) for r in rows)
    total_neu = sum(r.get('neutral_count',0) for r in rows)
    return {'positive': total_pos, 'negative': total_neg, 'neutral': total_neu, 'per_product': rows}
