#!/usr/bin/env python3
"""
Create an admin user for the local sqlite database.
Usage:
    python scripts/create_admin.py --username admin --password secret
If no password provided, reads from ADMIN_PASSWORD env or prompts.
"""
import os
import sys
import argparse

# Ensure project root is on sys.path so imports work when running the script directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db_utils import register_user, get_user_by_username, set_user_role
from database import db_init


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', '-u', default=os.environ.get('ADMIN_USER', 'admin'))
    parser.add_argument('--password', '-p', default=os.environ.get('ADMIN_PASSWORD'))
    parser.add_argument('--db', '-d', default=os.environ.get('DB_PATH', 'ecommerce.db'))
    args = parser.parse_args()

    username = args.username
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass(f'Password for {username}: ')

    # ensure DB schema initialized (adds role column if needed)
    db_init.init_database(db_path=args.db)

    # create user (will return existing user id if already exists)
    uid = register_user(username, password, db_path=args.db)
    if uid == -1:
        u = get_user_by_username(username, db_path=args.db)
        if u:
            uid = u['id']

    if uid and uid != -1:
        ok = set_user_role(uid, 'admin', db_path=args.db)
        if ok:
            print(f'Admin user "{username}" ready (id={uid}).')
        else:
            print(f'Failed to set role for user id={uid}.')
    else:
        print('Failed to create or locate user.')


if __name__ == '__main__':
    main()
