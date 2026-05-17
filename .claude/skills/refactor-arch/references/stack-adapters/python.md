# Stack Adapter — Python

Concrete signals, idioms, and code examples for Python projects. Loaded conditionally by `SKILL.md` after Phase 1 detects Python.

This adapter implements the language-specific layer described abstractly in `02-antipattern-catalog.md`, `04-architecture-guidelines.md`, and `05-refactor-playbook.md`.

---

## Framework Map

| Package in dependencies | Framework |
|---|---|
| `flask` | Flask |
| `fastapi` | FastAPI |
| `django` | Django |
| `starlette` | Starlette |
| `tornado` | Tornado |
| `aiohttp` | aiohttp |
| `bottle` | Bottle |
| `quart` | Quart |

Read the version from `requirements.txt` (`Flask==3.0.0`), `pyproject.toml` (`flask = "^3.0.0"`), or `Pipfile` (`flask = "*"`).

---

## ORM / Database Drivers

| Import | Layer |
|---|---|
| `from flask_sqlalchemy import SQLAlchemy` | SQLAlchemy via Flask integration |
| `from sqlalchemy import ...` | SQLAlchemy (Core or ORM) |
| `from django.db import models` | Django ORM |
| `from peewee import ...` | Peewee |
| `from tortoise import ...` | Tortoise ORM (async) |
| `import sqlite3` | Raw SQLite driver |
| `import psycopg2` / `import psycopg` | PostgreSQL driver |
| `import pymysql` / `import mysql.connector` | MySQL driver |
| `from pymongo import MongoClient` | MongoDB driver |

Raw-SQL signals: `cursor.execute(`, `conn.execute(`, presence of `CREATE TABLE` literals in source.

---

## Layout (idiomatic)

```
<project-root>/
├── .env.example
├── app.py                    # composition root
├── database.py               # db = SQLAlchemy() init
├── requirements.txt
├── config/
│   └── settings.py
├── models/
│   ├── user.py
│   └── task.py
├── services/
│   ├── user_service.py
│   └── task_service.py
├── controllers/
│   ├── user_controller.py
│   └── task_controller.py
├── routes/
│   ├── user_routes.py        # Blueprint per domain
│   └── task_routes.py
└── middleware/
    └── error_handler.py
```

**File naming:** `snake_case.py`. **Class naming:** `PascalCase`. **Function naming:** `snake_case`.

---

## AP-01 — Hardcoded Secrets (Python signals)

Patterns to grep for:
- `SECRET_KEY = "<literal>"`, `app.config['SECRET_KEY'] = "..."`
- `password = "..."`, `PASSWORD = "..."`
- `smtp_password = "..."`, `SMTP_PASS = "..."`
- `api_key = "..."`, `API_KEY = "..."`
- `DATABASE_URI = "postgresql://user:pass@host/db"` with inline credentials
- Class attributes: `class Config: SECRET = "..."`

What is NOT a finding: values loaded via `os.getenv(...)`, `os.environ[...]`, `dotenv_values(...)`, or a config object that wraps these calls.

---

## AP-02 — SQL Injection (Python signals)

Patterns to grep for:
- `cursor.execute("SELECT ... " + var)` — concatenation
- `cursor.execute(f"SELECT ... {var}")` — f-string
- `cursor.execute("SELECT ... %s" % var)` — `%` formatting
- `cursor.execute("SELECT ... {}".format(var))` — `.format()`
- Any `.execute(...)` / `.executemany(...)` whose first argument is the result of a string operation, not a static literal.

Safe forms: `cursor.execute("SELECT ... WHERE id = ?", (id,))` (SQLite), `cursor.execute("SELECT ... WHERE id = %s", (id,))` (psycopg2), or any ORM expression API.

---

## AP-03 — God File (Python signals)

- `app.py` or `controllers.py` > 200 LOC mixing `@app.route` decorators, ORM model classes, SQL queries, and business calculations.
- `models.py` containing both `db.Model` subclasses and HTTP-aware functions (importing `request`, `jsonify`).
- A single Flask blueprint module declaring more than two domains' routes.

---

## AP-04 — Dangerous Admin Endpoint (Python signals)

- `@app.route('/admin/query', methods=['POST']) def admin_query(): cursor.execute(request.json['query'])`
- Any handler reading `request.json.get('sql')`, `request.form['cmd']`, or similar and passing it to `eval`, `exec`, `compile`, `subprocess.run(shell=True)`, or a DB execute.

---

## AP-05 — Weak Crypto (Python signals)

- `hashlib.md5(password.encode()).hexdigest()` — MD5 for passwords
- `hashlib.sha1(...)` for passwords
- `base64.b64encode(...)` presented as hashing
- `crypto.Cipher.AES.new(key, mode)` without IV for non-ECB modes
- Comparison of passwords with `==` instead of `hmac.compare_digest` or library's `verify`

Recommended replacement: `passlib.hash.bcrypt` or `bcrypt` package; `cryptography.hazmat.primitives.ciphers` with AES-GCM.

---

## AP-06 — Business Logic in Handlers (Python signals)

- Inside a `@blueprint.route(...)` function: date arithmetic with `datetime`, price math, multi-step DB orchestration, calls to `send_email(...)` or external APIs.
- More than ~5 lines between the route decorator and the final `return jsonify(...)`.

---

## AP-07 — Global Mutable State (Python signals)

- Module-level `cache = {}` mutated inside request handlers.
- Module-level `counter = 0` with `counter += 1` inside a route.
- `class Foo: count = 0; Foo.count += 1` inside a handler.

---

## AP-08 — Async Pyramid (Python signals)

Less common in Python (callback-heavy code is rare). When present, look for:
- Nested `loop.run_in_executor` callbacks.
- Manually chained `asyncio.ensure_future` instead of `await`.
- Twisted-style deferred chains (`d.addCallback(...).addCallback(...)`).

---

## AP-09 — Missing Environment Configuration (Python signals)

- `app.run(debug=True, port=5000)` with literal arguments.
- `app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'` not from env.
- `python-dotenv` listed in `requirements.txt` but never imported.
- No `.env.example` at the project root.

---

## AP-10 — N+1 Queries (Python signals)

- A `for` loop iterating over `Model.query.all()` where each iteration calls `OtherModel.query.get(x.fk)`.
- ORM relationship attributes accessed in a loop without a prior `.options(joinedload(...))` or `.options(selectinload(...))`.

---

## AP-11 — Bare Exception Handling (Python signals)

- `except:` with no exception type — catches `KeyboardInterrupt`, `SystemExit`, `MemoryError`.
- `except Exception: pass` (silent swallow).
- `except Exception as e: return jsonify({'error': 'something went wrong'}), 500` without `logger.exception(...)`.

---

## AP-12 — Debug Mode (Python signals)

- `app.run(debug=True)` not gated by env check.
- `app.config['DEBUG'] = True` at module level.
- Flask's interactive `Werkzeug` debugger reachable on production.

---

## AP-13 — Duplicated Logic (Python signals)

- The same multi-line block appearing in `routes/*.py` and `models/*.py` (e.g., overdue calculation).
- Identical validation in multiple handler functions.

---

## AP-14 — Deprecated APIs (Python signals)

| Deprecated | Replacement | Removed in |
|---|---|---|
| `datetime.datetime.utcnow()` | `datetime.now(timezone.utc)` | Soft-deprecated in 3.12 |
| `flask.ext.*` | direct imports (`flask_sqlalchemy`, etc.) | Flask 1.0 |
| `@app.before_first_request` | `with app.app_context(): ...` in factory | Flask 3.0 |
| `werkzeug.contrib.*` | external packages or direct replacements | Werkzeug 1.0 |
| `Model.query` (SQLAlchemy) | `db.session.execute(select(Model))` | Soft-deprecated in SA 2.0 |
| `pkg_resources` | `importlib.resources` / `importlib.metadata` | setuptools deprecation |
| `imp` module | `importlib` | Removed in 3.12 |

---

## AP-15 — Magic Values (Python signals)

- `if order.status == 1:` — numeric status without a constant.
- `if user.role == 'admin':` repeated across files instead of `Role.ADMIN`.
- `return jsonify({...}), 404` repeated 10+ times instead of `from http import HTTPStatus`.

---

## AP-16 — Poor Names (Python signals)

- Variables named `x`, `d`, `t`, `r` outside short comprehensions.
- Function names like `do_thing`, `process_data`, `handle_it`.
- Abbreviations not in the project glossary: `usr`, `prd`, `ord`, `calc_ov`.

---

## PB-01 — Hardcoded Secrets → Environment Variables (Python)

**Before:**
```python
# app.py
app.config['SECRET_KEY'] = 'minha-chave-super-secreta-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.run(debug=True, port=5000)
```

**After:**
```python
# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY must be set')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
PORT = int(os.getenv('PORT', 5000))
```
```python
# app.py
from config.settings import SECRET_KEY, DATABASE_URL, DEBUG, PORT
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.run(debug=DEBUG, port=PORT)
```
```
# .env.example
SECRET_KEY=replace-me
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
PORT=5000
```

---

## PB-02 — SQL Injection → Parameterized Queries (Python)

**Before:**
```python
def get_product(id):
    return conn.execute("SELECT * FROM products WHERE id = " + str(id)).fetchone()

def search_products(name):
    return conn.execute(f"SELECT * FROM products WHERE name LIKE '%{name}%'").fetchall()
```

**After (minimum — placeholders):**
```python
def get_product(id):
    return conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()

def search_products(name):
    return conn.execute("SELECT * FROM products WHERE name LIKE ?", (f'%{name}%',)).fetchall()
```

**After (preferred — SQLAlchemy ORM):**
```python
from models.product import Product

def get_product(id):
    return Product.query.get_or_404(id)

def search_products(name):
    return Product.query.filter(Product.name.ilike(f'%{name}%')).all()
```

---

## PB-03 — God File → MVC (Python)

Decompose a single `controllers.py` or `models.py` (300+ LOC) into:

```
models/
    product.py        # class Product(db.Model) + to_dict()
    user.py
    order.py
services/
    product_service.py    # get_all, get_by_id, create, update, delete
    user_service.py
    order_service.py
controllers/
    product_controller.py # parse request → call service → jsonify
    user_controller.py
    order_controller.py
routes/
    product_routes.py     # Blueprint('products', __name__)
    user_routes.py
    order_routes.py
```

**Rule:** one entity per file per layer. Blueprints register controllers; controllers call services; services call models.

---

## PB-04 — Dangerous Admin Endpoint → Removal (Python)

**Before:**
```python
@app.route('/admin/query', methods=['POST'])
def admin_query():
    query = request.json.get('query')
    return jsonify(conn.execute(query).fetchall())
```

**After:** delete the endpoint. If a constrained subset is genuinely required:
```python
ALLOWED_REPORTS = {
    'user_count': 'SELECT COUNT(*) AS n FROM users',
    'order_count': 'SELECT COUNT(*) AS n FROM orders',
}

@admin_bp.route('/reports/<name>', methods=['GET'])
@require_admin_token
def admin_report(name):
    if name not in ALLOWED_REPORTS:
        return jsonify({'error': 'unknown report'}), 404
    row = db.session.execute(text(ALLOWED_REPORTS[name])).first()
    return jsonify(dict(row._mapping))
```

---

## PB-05 — Weak Crypto → bcrypt (Python)

**Before:**
```python
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()
```

**After:**
```python
from passlib.hash import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)
```

---

## PB-06 — Business Logic in Routes → Services (Python)

**Before:**
```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    for task in tasks:
        user = User.query.get(task.user_id)
        category = Category.query.get(task.category_id)
        is_overdue = task.due_date and task.status != 'completed' and datetime.utcnow() > task.due_date
        result.append({'id': task.id, 'title': task.title, 'is_overdue': is_overdue,
                       'user': user.name if user else None,
                       'category': category.name if category else None})
    return jsonify(result)
```

**After:**
```python
# services/task_service.py
class TaskService:
    @staticmethod
    def get_all_tasks():
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        return [t.to_dict() for t in tasks]

# controllers/task_controller.py
def get_tasks():
    return jsonify(TaskService.get_all_tasks()), 200

# routes/task_routes.py
task_bp.route('/tasks', methods=['GET'])(get_tasks)
```

---

## PB-07 — Async Pyramid → async/await (Python)

Rarely needed in Python. When found:

**Before:**
```python
loop.run_in_executor(None, fetch_user, uid, lambda u:
    loop.run_in_executor(None, fetch_orders, u.id, lambda os:
        loop.run_in_executor(None, fetch_payments, os, ...)))
```

**After:**
```python
async def checkout(uid):
    user = await fetch_user(uid)
    orders = await fetch_orders(user.id)
    payments = await fetch_payments(orders)
    return payments
```

---

## PB-08 — Global State → Encapsulation (Python)

**Before:**
```python
# utils.py
global_cache = {}
total_revenue = 0
```

**After:**
```python
# services/revenue_service.py
from threading import Lock

class RevenueService:
    def __init__(self):
        self._total = 0
        self._lock = Lock()
    def add(self, amount):
        with self._lock:
            self._total += amount
    @property
    def total(self):
        return self._total

revenue_service = RevenueService()
```

---

## PB-09 — N+1 → Eager Loading (Python)

**Before:**
```python
tasks = Task.query.all()
for task in tasks:
    user = User.query.get(task.user_id)
```

**After:**
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
```

Relationships on the model:
```python
class Task(db.Model):
    user = db.relationship('User', lazy='select')
    category = db.relationship('Category', lazy='select')
```

---

## PB-10 — Bare except → Specific Handling (Python)

**Before:**
```python
try:
    task = create_task(data)
    db.session.commit()
    return jsonify(task), 201
except:
    return jsonify({'error': 'something went wrong'}), 500
```

**After:**
```python
import logging
from sqlalchemy.exc import SQLAlchemyError
logger = logging.getLogger(__name__)

try:
    task = create_task(data)
    db.session.commit()
    return jsonify(task.to_dict()), 201
except ValueError as e:
    return jsonify({'error': str(e)}), 400
except SQLAlchemyError:
    db.session.rollback()
    logger.exception('database error creating task')
    return jsonify({'error': 'database error'}), 500
```

---

## PB-11 — Deprecated APIs (Python)

**`datetime.utcnow()` → timezone-aware:**
```python
# Before
created_at = datetime.utcnow()
# After
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

**`Model.query` (SQLAlchemy 1.x) → `db.session.execute(select(...))`:**
```python
# Before
users = User.query.all()
# After
from sqlalchemy import select
users = db.session.execute(select(User)).scalars().all()
```

**`@app.before_first_request` (Flask) → app factory init:**
```python
# Before
@app.before_first_request
def init_db():
    db.create_all()
# After — in the app factory
def create_app():
    app = Flask(__name__)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app
```

---

## PB-12 — Duplicated Logic → Model Method (Python)

**Before:** overdue check in both `routes/task_routes.py` and `models/task.py`.

**After:** keep one canonical implementation on the model.
```python
# models/task.py
def is_overdue(self) -> bool:
    if not self.due_date or self.status == 'completed':
        return False
    return datetime.now(timezone.utc) > self.due_date.replace(tzinfo=timezone.utc)
```
Everywhere else: `task.is_overdue()`.

---

## PB-13 — Magic Values → Constants (Python)

**Before:**
```python
if order.status == 1: ...
if user.role == 'admin': ...
return jsonify({...}), 404
```

**After:**
```python
# constants.py
from enum import Enum

class OrderStatus(Enum):
    PENDING = 1
    PAID = 2
    SHIPPED = 3
    CANCELLED = 4

class Role(str, Enum):
    ADMIN = 'admin'
    USER = 'user'

# usage
from http import HTTPStatus
if order.status == OrderStatus.PENDING.value: ...
if user.role == Role.ADMIN: ...
return jsonify({...}), HTTPStatus.NOT_FOUND
```

---

## PB-14 — Poor Names → Intent-Revealing (Python)

**Before:** `def proc(d): ...`, `usr = ...`, `overdue = True`

**After:** `def process_payment(data): ...`, `user = ...`, `is_overdue = True`. Follow PEP 8 (`snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for module-level constants).

---

## Boot & Validation

**Run command (Flask):**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# if a seed script exists:
python seed.py
python app.py
```

**Health probe:**
```bash
until curl -sf http://127.0.0.1:5000/ > /dev/null; do sleep 1; done
```

**Common ports:** Flask 5000, FastAPI/Uvicorn 8000, Django 8000.
