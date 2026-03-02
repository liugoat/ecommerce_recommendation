"""
简单情感分析流水线（基于词典），处理 `reviews` 表并写入 `product_sentiment` 表。

用法：
  python -m data_processing.sentiment
"""
import os
import sys
import re
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import query_reviews_by_product, upsert_product_sentiment, aggregate_all_product_sentiments
from database.db_utils import get_db_connection

# 简单词典（示例，可扩充）
POSITIVE = set(['好', '不错', '喜欢', '满意', '推荐', '优秀', '棒', '爱', '喜欢', '超赞', 'perfect', 'good', 'great'])
NEGATIVE = set(['差', '失望', '糟糕', '不行', '退货', '差评', '垃圾', '坏', 'worst', 'bad'])


def score_text(text: str) -> float:
    if not text:
        return 0.0
    s = re.sub(r'\s+', '', text.lower())
    pos = sum(1 for w in POSITIVE if w in s)
    neg = sum(1 for w in NEGATIVE if w in s)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def process_product(product_id: int, db_path: str = 'ecommerce.db'):
    reviews = query_reviews_by_product(product_id, db_path)
    if not reviews:
        return None
    scores = []
    pos = neg = neu = 0
    for r in reviews:
        sc = score_text(r.get('content') or '')
        scores.append(sc)
        if sc > 0:
            pos += 1
        elif sc < 0:
            neg += 1
        else:
            neu += 1

    avg = sum(scores) / len(scores) if scores else 0.0
    upsert_product_sentiment(product_id, avg, pos, neg, neu, db_path)
    return {'product_id': product_id, 'avg': avg, 'pos': pos, 'neg': neg, 'neu': neu}


def process_all(db_path: str = 'ecommerce.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT product_id FROM reviews')
    rows = cursor.fetchall()
    conn.close()
    results = []
    for (pid,) in rows:
        r = process_product(pid, db_path)
        if r:
            results.append(r)
    return results


if __name__ == '__main__':
    res = process_all('ecommerce.db')
    print('处理完成，更新情感结果数量:', len(res))
