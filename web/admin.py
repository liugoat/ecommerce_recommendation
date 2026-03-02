from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
import os
import sys
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_init import get_db_connection
from database.db_utils import get_product_by_id, create_product, update_product, delete_product, get_orders, update_order_status, export_orders_csv
from database.db_utils import get_all_users, set_user_role, get_recent_behaviors

admin_bp = Blueprint('admin', __name__, template_folder='templates')


def _is_admin():
    # 支持两种管理员标记：老的 is_admin 或者用户 role 为 admin
    return session.get('is_admin') or session.get('role') == 'admin'


@admin_bp.before_request
def _require_admin_for_protected():
    # 允许未登录访问的视图名单
    allowed = {'admin.admin_login', 'admin.admin_logout'}
    # request.endpoint 可能为 None（静态文件等），保守处理
    try:
        ep = request.endpoint
    except Exception:
        ep = None

    if ep and ep not in allowed:
        # 如果不是登录页并且没有管理员权限，重定向到登录页
        if not _is_admin():
            return redirect(url_for('admin.admin_login'))


@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd and pwd == current_app.config.get('ADMIN_PASSWORD', 'admin'):
            # 标记管理员会话；同时设置 role 与 username 以保持与普通登录一致的会话字段
            session['is_admin'] = True
            session['role'] = 'admin'
            session['username'] = 'admin'
            # 可选：不设置 user_id，管理员使用独立会话标识
            return redirect(url_for('admin.index'))
        else:
            return render_template('admin_login.html', error='密码错误')
    return render_template('admin_login.html')


@admin_bp.route('/admin/logout')
def admin_logout():
    # 清理管理员相关会话字段
    session.pop('is_admin', None)
    session.pop('role', None)
    session.pop('username', None)
    session.pop('user_id', None)
    # 登出后返回首页，允许用户选择普通登录或其它操作
    return redirect(url_for('index'))


@admin_bp.route('/admin')
def index():
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection(current_app.config.get('DB_PATH', 'ecommerce.db'))
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    products_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM user_behavior')
    behaviors_count = cursor.fetchone()[0]
    conn.close()

    return render_template('admin_index.html', products_count=products_count, users_count=users_count, behaviors_count=behaviors_count)


@admin_bp.route('/admin/users')
def users():
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    users = get_all_users(current_app.config.get('DB_PATH', 'ecommerce.db'))
    return render_template('admin_users.html', users=users)


@admin_bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
def user_set_role(user_id):
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    role = request.form.get('role')
    if role not in ('user', 'admin'):
        role = 'user'
    set_user_role(user_id, role, current_app.config.get('DB_PATH', 'ecommerce.db'))
    return redirect(url_for('admin.users'))


@admin_bp.route('/admin/products')
def products():
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    conn = get_db_connection(current_app.config.get('DB_PATH', 'ecommerce.db'))
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price, sales, category FROM products ORDER BY id DESC LIMIT 200')
    rows = cursor.fetchall()
    conn.close()
    products = [{'id': r[0], 'name': r[1], 'price': r[2], 'sales': r[3], 'category': r[4]} for r in rows]
    return render_template('admin_products.html', products=products)


@admin_bp.route('/admin/products/new', methods=['GET', 'POST'])
def product_new():
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    if request.method == 'POST':
        data = dict(request.form)
        pid = create_product(data, current_app.config.get('DB_PATH', 'ecommerce.db'))
        return redirect(url_for('admin.products'))
    return render_template('admin_product_form.html', product=None)


@admin_bp.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    if request.method == 'POST':
        data = dict(request.form)
        update_product(product_id, data, current_app.config.get('DB_PATH', 'ecommerce.db'))
        return redirect(url_for('admin.products'))
    prod = get_product_by_id(product_id, current_app.config.get('DB_PATH', 'ecommerce.db'))
    return render_template('admin_product_form.html', product=prod)


@admin_bp.route('/admin/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    delete_product(product_id, current_app.config.get('DB_PATH', 'ecommerce.db'))
    return redirect(url_for('admin.products'))


@admin_bp.route('/admin/orders')
def orders():
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    orders = get_orders(500, current_app.config.get('DB_PATH', 'ecommerce.db'))
    return render_template('admin_orders.html', orders=orders)


@admin_bp.route('/admin/orders/<int:order_id>/status', methods=['POST'])
def orders_update_status(order_id):
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    status = request.form.get('status')
    update_order_status(order_id, status, current_app.config.get('DB_PATH', 'ecommerce.db'))
    return redirect(url_for('admin.orders'))


@admin_bp.route('/admin/orders/export')
def orders_export():
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    path = export_orders_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'orders_export.csv'), current_app.config.get('DB_PATH', 'ecommerce.db'))
    return redirect('/' + os.path.relpath(path).replace('\\', '/'))


@admin_bp.route('/admin/logs')
def logs():
    if not _is_admin():
        return redirect(url_for('admin.admin_login'))
    logs = get_recent_behaviors(200, current_app.config.get('DB_PATH', 'ecommerce.db'))
    return render_template('admin_logs.html', logs=logs)
