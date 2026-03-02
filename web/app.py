"""
Web界面模块
使用Flask提供电商平台推荐系统的前端界面
"""
import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommendation.recommender import get_recommendations, get_homepage_recommendations
from database.db_utils import query_all_products, register_user, login_user, insert_user_behavior, get_user_behaviors
from database.db_utils import insert_favorite, remove_favorite, get_user_favorites
from database.db_utils import insert_review
from data_processing.sentiment import process_product

# 注册管理 blueprint（将在创建 app 之后注册）
from web.admin import admin_bp

# Analytics APIs
from analytics.analytics import sales_trend, top_n_products, revenue_by_category, price_distribution, review_sentiment_overview

# 定义数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ecommerce.db")

app = Flask(__name__, template_folder='templates', static_folder='static')
# 配置可通过环境变量覆盖，方便部署和测试
app.config['DB_PATH'] = DB_PATH
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'admin')
app.secret_key = os.environ.get('FLASK_SECRET', 'change_me_secret')  # 用于session加密，可从环境变量读取

# 注册 admin blueprint
app.register_blueprint(admin_bp)

# 确保静态文件目录存在
static_dir = os.path.join(os.path.dirname(__file__), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 确保模板目录存在
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
if not os.path.exists(template_dir):
    os.makedirs(template_dir)

# RBAC 装饰器：可在路由上使用
def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not (session.get('is_admin') or session.get('role') == 'admin'):
            return jsonify({'error': 'admin required'}), 403
        return f(*args, **kwargs)
    return wrapped


def role_required(role: str):
    """装饰器：检查当前登录用户是否具有指定角色（或为admin）。"""
    def deco(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_role = session.get('role')
            if user_role == 'admin' or user_role == role:
                return f(*args, **kwargs)
            return jsonify({'error': 'role required', 'required': role}), 403
        return wrapped
    return deco

def _parse_categories(raw_category):
    """Normalize category field to list[str]."""
    if raw_category is None:
        return []

    if isinstance(raw_category, (list, tuple, set)):
        return [str(x).strip() for x in raw_category if str(x).strip()]

    if isinstance(raw_category, str):
        c = raw_category.strip()
        if not c:
            return []

        if c.startswith('['):
            try:
                import json as _json

                parsed = _json.loads(c)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass

        for sep in ['|', '/', ',', ';']:
            if sep in c:
                return [x.strip() for x in c.split(sep) if x.strip()]

        return [c]

    return [str(raw_category).strip()]


def _format_category_display(raw_category):
    cats = _parse_categories(raw_category)
    return ' / '.join(cats) if cats else '未分类'


def _with_category_display(products):
    out = []
    for p in products:
        item = dict(p)
        item['category_list'] = _parse_categories(item.get('category'))
        item['category_display'] = _format_category_display(item.get('category'))
        out.append(item)
    return out




@app.route('/')
def index():
    """???????????????????"""
    user_id = session.get('user_id')
    bundles = get_homepage_recommendations(user_id=user_id, top_n=10, db_path=DB_PATH)

    popular_products = _with_category_display(bundles.get('popular', []))
    new_arrival_products = _with_category_display(bundles.get('new_arrivals', []))
    personalized_products = _with_category_display(bundles.get('personalized', []))
    similar_products = _with_category_display(bundles.get('similar', []))

    return render_template(
        'index.html',
        popular_products=popular_products,
        new_arrival_products=new_arrival_products,
        personalized_products=personalized_products,
        similar_products=similar_products,
        logged_in=('user_id' in session),
        username=session.get('username')
    )


@app.route('/user/<int:user_id>')

def user_recommendations(user_id):
    """展示特定用户的推荐商品"""
    # 检查是否是当前登录用户
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('index'))
        
    recommendations = _with_category_display(get_recommendations(user_id=user_id, top_n=10, db_path=DB_PATH))
    return render_template('user_recommendations.html', 
                           recommendations=recommendations, 
                           user_id=user_id,
                           logged_in=True,
                           username=session['username'])


@app.route('/public/user/<int:user_id>')
def public_user_recommendations(user_id):
    """公共接口，展示特定用户的推荐商品（无需登录）"""
    recommendations = _with_category_display(get_recommendations(user_id=user_id, top_n=10, db_path=DB_PATH))
    return render_template('user_recommendations.html', 
                           recommendations=recommendations, 
                           user_id=user_id,
                           logged_in='user_id' in session,
                           username=session.get('username') if 'user_id' in session else None)


@app.route('/product/<int:product_id>')
def similar_products(product_id):
    """展示与指定商品相似的商品"""
    recommendations = _with_category_display(get_recommendations(product_id=product_id, top_n=10, db_path=DB_PATH))
    product = next((p for p in query_all_products(db_path=DB_PATH) if p['id'] == product_id), None)
    if product:
        product = dict(product)
        product['category_list'] = _parse_categories(product.get('category'))
        product['category_display'] = _format_category_display(product.get('category'))
    
    # 记录用户查看商品的行为（如果用户已登录）
    if 'user_id' in session:
        insert_user_behavior(session['user_id'], product_id, 'view', DB_PATH)
    
    return render_template('similar_products.html', 
                           recommendations=recommendations, 
                           product=product)


@app.route('/all_products')
def all_products():
    """??????"""
    args = request.args
    category = args.get('category')
    q = args.get('q')
    sort = args.get('sort')  # sales|price_asc|price_desc|rating|new
    page = int(args.get('page', 1))
    size = int(args.get('size', 24))

    products = query_all_products(db_path=DB_PATH)

    cats = set()
    for p in products:
        for c in _parse_categories(p.get('category')):
            cats.add(c)
    categories = sorted(list(cats))

    if category:
        products = [p for p in products if category in _parse_categories(p.get('category'))]
    if q:
        products = [p for p in products if q.lower() in (p.get('name') or '').lower()]

    if sort == 'sales':
        products.sort(key=lambda x: x.get('sales') or 0, reverse=True)
    elif sort == 'price_asc':
        products.sort(key=lambda x: x.get('price') or 0)
    elif sort == 'price_desc':
        products.sort(key=lambda x: x.get('price') or 0, reverse=True)
    elif sort == 'rating':
        products.sort(key=lambda x: x.get('rating') or 0, reverse=True)
    elif sort == 'new':
        products.sort(key=lambda x: (x.get('crawl_time') or '', x.get('id') or 0), reverse=True)

    total = len(products)
    start = (page - 1) * size
    end = start + size
    items = _with_category_display(products[start:end])

    return render_template('all_products.html', products=items, categories=categories, selected_category=category, sort=sort, page=page, size=size, total=total)


@app.route('/api/products')
def api_products():
    """???????????????API"""
    args = request.args
    category = args.get('category')
    q = args.get('q')
    sort = args.get('sort')  # sales|price_asc|price_desc|rating|new
    page = int(args.get('page', 1))
    size = int(args.get('size', 20))
    min_price = args.get('min_price')
    max_price = args.get('max_price')

    products = query_all_products(db_path=DB_PATH)

    if category:
        products = [p for p in products if category in _parse_categories(p.get('category'))]
    if q:
        products = [p for p in products if q.lower() in (p.get('name') or '').lower()]
    if min_price:
        try:
            min_p = float(min_price)
            products = [p for p in products if (p.get('price') or 0) >= min_p]
        except Exception:
            pass
    if max_price:
        try:
            max_p = float(max_price)
            products = [p for p in products if (p.get('price') or 0) <= max_p]
        except Exception:
            pass

    if sort == 'sales':
        products.sort(key=lambda x: x.get('sales') or 0, reverse=True)
    elif sort == 'price_asc':
        products.sort(key=lambda x: x.get('price') or 0)
    elif sort == 'price_desc':
        products.sort(key=lambda x: x.get('price') or 0, reverse=True)
    elif sort == 'rating':
        products.sort(key=lambda x: x.get('rating') or 0, reverse=True)
    elif sort == 'new':
        products.sort(key=lambda x: (x.get('crawl_time') or '', x.get('id') or 0), reverse=True)

    total = len(products)
    start = (page - 1) * size
    end = start + size
    items = _with_category_display(products[start:end])

    return jsonify({
        'total': total,
        'page': page,
        'size': size,
        'items': items
    })


@app.route('/api/recommend/<int:user_id>')

def api_recommendations(user_id):
    """API接口，返回用户的推荐商品（JSON格式）"""
    recommendations = get_recommendations(user_id=user_id, top_n=10, db_path=DB_PATH)
    return jsonify(recommendations)


@app.route('/api/product/<int:product_id>')
def api_product_detail(product_id):
    products = query_all_products(db_path=DB_PATH)
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'not found'}), 404

    # 相似推荐
    similar = get_recommendations(product_id=product_id, top_n=10, db_path=DB_PATH)

    return jsonify({'product': product, 'similar': similar})


@app.route('/api/reviews', methods=['POST'])
def api_post_review():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    rating = int(data.get('rating', 0))
    content = data.get('content', '')
    user_id = session.get('user_id')
    if not product_id:
        return jsonify({'error': 'product_id required'}), 400
    rid = insert_review(product_id, user_id, rating, content, DB_PATH)
    # 更新该商品情感汇总（同步）
    try:
        process_product(product_id, DB_PATH)
    except Exception:
        pass
    return jsonify({'status': 'ok', 'review_id': rid})


@app.route('/api/reviews/<int:product_id>')
def api_get_reviews(product_id):
    from database.db_utils import query_reviews_by_product
    rows = query_reviews_by_product(product_id, db_path=DB_PATH)
    return jsonify(rows)


@app.route('/reviews/form_submit', methods=['POST'])
def reviews_form_submit():
    """表单回退：在没有fetch的环境下提交评论并重定向回商品页面"""
    product_id = request.form.get('product_id')
    rating = int(request.form.get('rating', 0))
    content = request.form.get('content', '')
    user_id = session.get('user_id')
    try:
        product_id = int(product_id)
    except Exception:
        return redirect(request.referrer or url_for('all_products'))
    insert_review(product_id, user_id, rating, content, DB_PATH)
    try:
        process_product(product_id, DB_PATH)
    except Exception:
        pass
    return redirect(request.referrer or url_for('product', product_id=product_id))


@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
def api_favorites():
    if request.method == 'GET':
        if 'user_id' not in session:
            return jsonify({'error': 'not logged in'}), 401
        favs = get_user_favorites(session['user_id'], DB_PATH)
        return jsonify(favs)

    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'error': 'not logged in'}), 401
        data = request.get_json() or {}
        pid = data.get('product_id')
        if not pid:
            return jsonify({'error': 'product_id required'}), 400
        insert_favorite(session['user_id'], pid, DB_PATH)
        return jsonify({'status': 'ok'})

    if request.method == 'DELETE':
        if 'user_id' not in session:
            return jsonify({'error': 'not logged in'}), 401
        data = request.get_json() or {}
        pid = data.get('product_id')
        if not pid:
            return jsonify({'error': 'product_id required'}), 400
        remove_favorite(session['user_id'], pid, DB_PATH)
        return jsonify({'status': 'ok'})


@app.route('/favorites/form_toggle', methods=['POST'])
def favorites_form_toggle():
    """表单回退接口：支持在无 fetch 的环境下通过表单提交收藏/取消收藏"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    pid = request.form.get('product_id')
    action = request.form.get('action', 'add')
    try:
        pid = int(pid)
    except Exception:
        return redirect(request.referrer or url_for('all_products'))

    if action == 'add':
        insert_favorite(session['user_id'], pid, DB_PATH)
    else:
        remove_favorite(session['user_id'], pid, DB_PATH)

    return redirect(request.referrer or url_for('all_products'))


# Dashboard pages and API
@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/api/analytics/sales_trend')
@admin_required
def api_sales_trend():
    days = int(request.args.get('days', 30))
    data = sales_trend(days=days, db_path=DB_PATH)
    return jsonify(data)


@app.route('/api/analytics/top_products')
@admin_required
def api_top_products():
    n = int(request.args.get('n', 10))
    data = top_n_products(n=n, db_path=DB_PATH)
    return jsonify(data)


@app.route('/api/analytics/revenue_by_category')
@admin_required
def api_revenue_by_category():
    data = revenue_by_category(db_path=DB_PATH)
    return jsonify(data)


@app.route('/api/analytics/price_distribution')
@admin_required
def api_price_distribution():
    category = request.args.get('category')
    data = price_distribution(category=category, db_path=DB_PATH)
    return jsonify(data)


@app.route('/api/analytics/review_sentiment')
@admin_required
def api_review_sentiment():
    data = review_sentiment_overview(db_path=DB_PATH)
    return jsonify(data)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_id = register_user(username, password, DB_PATH)
        if user_id != -1:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('register.html', error="用户名已存在")
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_id = login_user(username, password, DB_PATH)
        if user_id != -1:
            session['user_id'] = user_id
            session['username'] = username
            # 写入 role 到 session（用于快速 RBAC）
            try:
                from database.db_utils import get_user_by_username
                u = get_user_by_username(username, DB_PATH)
                session['role'] = u.get('role') if u else None
            except Exception:
                session['role'] = None
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="用户名或密码错误")
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """用户登出"""
    session.pop('user_id', None)
    session.pop('username', None)
    # 清理可能残留的 role 和 is_admin 标志
    session.pop('role', None)
    session.pop('is_admin', None)
    return redirect(url_for('index'))


@app.route('/api/record_click/<int:product_id>')
def record_click(product_id):
    """API接口，记录用户点击商品的行为"""
    if 'user_id' in session:
        insert_user_behavior(session['user_id'], product_id, 'click', DB_PATH)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'not logged in'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
