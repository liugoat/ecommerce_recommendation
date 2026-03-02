import os
from flask import Flask


def validate_templates(template_dir: str):
    app = Flask(__name__, template_folder=template_dir)
    env = app.jinja_env
    errors = []
    for root, dirs, files in os.walk(template_dir):
        for fn in files:
            if not fn.endswith('.html'):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, template_dir)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    src = f.read()
                env.parse(src)
            except Exception as e:
                errors.append((rel, str(e)))
    return errors


if __name__ == '__main__':
    tpl_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web', 'templates')
    errs = validate_templates(tpl_dir)
    if not errs:
        print('All templates parsed successfully')
    else:
        print('Template errors found:')
        for r, e in errs:
            print(f'- {r}: {e}')
