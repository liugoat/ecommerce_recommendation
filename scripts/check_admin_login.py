#!/usr/bin/env python3
"""
Check admin login and protected API access using Flask test client.
Runs three checks:
 - access analytics without login -> expect 403
 - login as admin and access analytics -> expect 200
 - login as non-admin and access analytics -> expect 403
"""
import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from web import app as webapp
from database.db_utils import register_user, set_user_role

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASSWORD', 'admin')
TEST_USER = 'test_user_for_check'
TEST_PASS = 'testpass'


def ensure_test_users():
    # ensure admin exists and is admin
    aid = register_user(ADMIN_USER, ADMIN_PASS, db_path=webapp.app.config.get('DB_PATH', 'ecommerce.db'))
    set_user_role(aid, 'admin', db_path=webapp.app.config.get('DB_PATH', 'ecommerce.db'))
    # ensure normal test user
    tid = register_user(TEST_USER, TEST_PASS, db_path=webapp.app.config.get('DB_PATH', 'ecommerce.db'))
    set_user_role(tid, 'user', db_path=webapp.app.config.get('DB_PATH', 'ecommerce.db'))


def run_checks():
    ensure_test_users()
    client = webapp.app.test_client()

    print('1) Access analytics without login (expect 403)')
    r = client.get('/api/analytics/sales_trend')
    print('status:', r.status_code, r.get_json())

    print('\n2) Login as normal user and access analytics (expect 403)')
    r = client.post('/login', data={'username': TEST_USER, 'password': TEST_PASS}, follow_redirects=True)
    r2 = client.get('/api/analytics/sales_trend')
    print('status after login as user:', r2.status_code, r2.get_json())

    print('\n3) Login as admin and access analytics (expect 200)')
    # logout first
    client.get('/logout')
    r = client.post('/login', data={'username': ADMIN_USER, 'password': ADMIN_PASS}, follow_redirects=True)
    r2 = client.get('/api/analytics/sales_trend')
    print('status after login as admin:', r2.status_code, r2.get_json())


if __name__ == '__main__':
    run_checks()
