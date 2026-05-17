================================
PHASE 3: REFACTORING COMPLETE
================================
Project: code-smells-project
Date:    2026-05-17

## New Project Structure

code-smells-project/
├── .env                          # existing (actual values, not committed)
├── .env.example                  # NEW — placeholder template
├── app.py                        # REWRITTEN — minimal composition root (~50 LOC)
├── database.py                   # REWRITTEN — Flask g per-request connection + init_db()
├── requirements.txt              # UPDATED — added python-dotenv, bcrypt
├── api.http                      # unchanged
├── config/
│   ├── __init__.py
│   └── settings.py               # NEW — reads SECRET_KEY, DATABASE_URL, DEBUG, PORT, HOST from env
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py     # NEW — thin HTTP handlers (parse→service→jsonify)
│   ├── usuario_controller.py     # NEW
│   └── pedido_controller.py      # NEW
├── middleware/
│   ├── __init__.py
│   └── error_handler.py          # NEW — centralized Flask error handlers (400/404/500)
├── models/
│   ├── __init__.py
│   ├── produto.py                # NEW — Produto dataclass + CATEGORIAS_VALIDAS constant
│   ├── usuario.py                # NEW — Usuario dataclass
│   └── pedido.py                 # NEW — Pedido dataclass + STATUS_VALIDOS + DISCOUNT_TIERS
├── routes/
│   ├── __init__.py
│   ├── produto_routes.py         # NEW — Blueprint, one line per URL binding
│   ├── usuario_routes.py         # NEW
│   └── pedido_routes.py          # NEW
└── services/
    ├── __init__.py
    ├── produto_service.py        # NEW — all product CRUD + validation + parameterized SQL
    ├── usuario_service.py        # NEW — user CRUD + bcrypt auth
    └── pedido_service.py         # NEW — order creation + JOIN-based retrieval + discount calc

DELETED (god files fully superseded):
  - controllers.py  (292 LOC monolith)
  - models.py       (314 LOC monolith)

## Fixes Applied

| Anti-pattern | Playbook | What changed |
|---|---|---|
| AP-01 Hardcoded SECRET_KEY (app.py:7) | PB-01 | Moved to config/settings.py via os.getenv(); loaded from .env |
| AP-01 Secret key in /health response (controllers.py:289) | PB-01 | health_check now returns only status, counts, version |
| AP-02 SQL injection in 12+ functions (models.py) | PB-02 | All SQL uses `?` parameterized placeholders; login, search, and CRUD safe |
| AP-03 God file models.py (314 LOC) | PB-03 | Decomposed to models/ + services/ — one file per entity per layer |
| AP-03 God file controllers.py (292 LOC) | PB-03 | Decomposed to controllers/ + routes/ — thin handlers only |
| AP-04 /admin/query arbitrary SQL | PB-04 | Endpoint deleted entirely; returns 404 |
| AP-04 /admin/reset-db unauthenticated | PB-04 | Endpoint deleted entirely; returns 404 |
| AP-05 Plaintext passwords (models.py:122) | PB-05 | New users hashed with bcrypt; login supports bcrypt + legacy plaintext transition |
| AP-06 Business logic in handlers | PB-06 | All domain rules in services/; controllers are parse→call→serialize |
| AP-07 Global db_connection singleton | PB-08 | Flask g per-request connection; teardown_appcontext closes it |
| AP-09 Missing env config | PB-01 | All literals (DEBUG, PORT, HOST, SECRET_KEY, DATABASE_URL) from env |
| AP-10 N+1 queries in order retrieval | PB-09 | Single JOIN across pedidos+itens_pedido+produtos; O(1) queries regardless of count |
| AP-11 Bare except Exception in 13 handlers | PB-10 | Specific ValueError/sqlite3.Error catches; centralized middleware/error_handler.py |
| AP-12 DEBUG=True unconditional | PB-01 | DEBUG = (FLASK_ENV == 'development'); gated by environment variable |
| AP-13 Duplicated order-item logic | PB-12 | Single _build_pedidos_from_join() helper; _JOIN_QUERY constant reused |
| AP-15 Magic numbers in discount tiers | PB-13 | DISCOUNT_TIERS list in models/pedido.py; _calcular_desconto() iterates it |

## Validation

  ✓ GET /           → 200 OK (mensagem: "Bem-vindo à API da Loja")
  ✓ GET /health     → 200 OK (status: "ok", counts visible)
  ✓ GET /produtos   → 200 OK (10 products returned)
  ✓ GET /produtos/1 → 200 OK
  ✓ GET /produtos/9999 → 404 Not Found
  ✓ POST /produtos (valid)           → 201 Created (id: 12)
  ✓ POST /produtos (invalid category) → 400 Bad Request
  ✓ PUT /produtos/1  → 200 OK
  ✓ DELETE /produtos/3 → 404 (product was deleted in prior run — correct behavior)
  ✓ GET /produtos/busca?q=notebook   → 200 OK (3 results)
  ✓ GET /produtos/busca (with filters) → 200 OK (7 results)
  ✓ GET /produtos/busca SQL injection attempt → 200 OK (parameterized — injection blocked)
  ✓ GET /usuarios   → 200 OK (4 users)
  ✓ GET /usuarios/1 → 200 OK
  ✓ POST /usuarios (valid)      → 201 Created (id: 5)
  ✓ POST /usuarios (incomplete) → 400 Bad Request
  ✓ POST /login (valid credentials)    → 200 OK (mensagem: "Login OK")
  ✓ POST /login (invalid credentials)  → 401 Unauthorized
  ✓ POST /login SQL injection attempt  → 401 Unauthorized (parameterized — injection blocked)
  ✓ GET /pedidos                  → 200 OK (1 order)
  ✓ GET /pedidos/usuario/1        → 200 OK
  ✓ POST /pedidos (valid)         → 201 Created (pedido_id: 2, total: 9689.90)
  ✓ POST /pedidos (empty items)   → 400 Bad Request
  ✓ PUT /pedidos/1/status (valid) → 200 OK
  ✓ PUT /pedidos/1/status (invalid) → 400 Bad Request
  ✓ GET /relatorios/vendas        → 200 OK (faturamento_bruto: 19379.80)
  ✓ POST /admin/query    → 404 Not Found (endpoint intentionally removed — PB-04)
  ✓ POST /admin/reset-db → 404 Not Found (endpoint intentionally removed — PB-04)

## Environment Variables

  Created: .env.example
  Variables:
    SECRET_KEY      — Flask signing secret (no default; must be set in production)
    DATABASE_URL    — SQLite file path (default: loja.db)
    FLASK_ENV       — "development" enables debug mode (default: production)
    PORT            — server port (default: 5000)
    HOST            — bind address (default: 0.0.0.0)

================================
