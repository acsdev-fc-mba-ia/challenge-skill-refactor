================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-05-17

## Summary
CRITICAL: 7 | HIGH: 3 | MEDIUM: 4 | LOW: 1
Total findings: 15

## Findings

### [CRITICAL] Hardcoded Secrets / Credentials — Secret Key in Source
File: app.py:7
Description: `app.config["SECRET_KEY"]` is assigned the literal string `"minha-chave-super-secreta-123"` directly in app.py. The value is committed to version control and visible to anyone with repository access. A .env file exists at the project root but is never loaded — `python-dotenv` is absent from requirements.txt and no `load_dotenv()` call exists anywhere.
Impact: Any user with read access to the repository can forge session cookies and impersonate any authenticated user.
Recommendation: Add `python-dotenv` to requirements.txt, call `load_dotenv()` in app.py, and read the key with `os.getenv('SECRET_KEY')`. Rotate the current key immediately.

### [CRITICAL] Hardcoded Secrets / Credentials — Secret Key Exposed via HTTP
File: controllers.py:289
Description: The `health_check()` function returns `"secret_key": "minha-chave-super-secreta-123"` as a top-level field in its JSON response. The signing secret is broadcast to any HTTP client that calls `GET /health`, compounding the version-control exposure with a live network exposure.
Impact: Any unauthenticated caller of `/health` obtains the signing secret, enabling session forgery without repository access.
Recommendation: Remove `secret_key`, `debug`, and `db_path` from the health response entirely. Return only operational status fields.

### [CRITICAL] SQL Injection via String Interpolation
File: models.py:28-314
Description: At least 12 SQL statements are assembled via Python string concatenation from caller-controlled values. Critical instances: `login_usuario()` (line 109) builds `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` — allowing authentication bypass with `' OR '1'='1' --`; `buscar_produtos()` (lines 289-296) appends the user-supplied `termo` and `categoria` query-string parameters directly into the WHERE clause; `criar_produto()` (lines 47-49) concatenates `nome`, `descricao`, and `categoria` from request JSON into an INSERT statement. Identical patterns appear in `get_produto_por_id()` (line 28), `atualizar_produto()` (lines 57-60), `deletar_produto()` (line 68), `get_usuario_por_id()` (line 92), `criar_usuario()` (lines 126-129), and throughout `criar_pedido()` (lines 140-165).
Impact: Attackers can bypass authentication, read all user credentials, modify or destroy any data, and potentially escalate to OS-level access through the SQLite engine.
Recommendation: Replace every concatenated query with parameterized placeholders (`?`) as the second argument to `cursor.execute()`. For search, use `LIKE ?` with `f'%{term}%'` as the parameter, never interpolated into the string.

### [CRITICAL] God File — Data Access + Business Logic + Transformation
File: models.py:1-314
Description: `models.py` (314 LOC) simultaneously contains raw SQL data access for all four entities, domain business logic (`criar_pedido()` lines 133-169 performs stock validation and total calculation; `relatorio_vendas()` lines 235-273 applies a tiered discount algorithm), and presentation-layer data transformation (every function builds and returns Python dicts). It is called a "model" file but performs responsibilities that belong in at least three separate layers.
Impact: Cannot unit-test the discount algorithm without a live database. A change to the SQL schema breaks unrelated business rules in the same file. Onboarding cost is high because intent is buried across 314 lines.
Recommendation: Decompose into `models/` (entity definitions), `services/` (business logic including discount and stock management), and parameterized repository helpers. Follow PB-03 and PB-06 in the playbook.

### [CRITICAL] God File — HTTP Handling + Domain Validation Mixed
File: controllers.py:1-292
Description: `controllers.py` (292 LOC) mixes HTTP request parsing, multi-step input validation (field presence, range checks, category allow-list at lines 52-54, status allow-list at line 242), domain notifications simulated inline (`criar_pedido()` lines 208-210 prints EMAIL/SMS/PUSH strings), and status-machine transition side-effects (`atualizar_status_pedido()` lines 247-250). No layer boundary separates HTTP concerns from domain concerns.
Impact: Every handler requires a live Flask request context to test. Adding a new notification channel means editing the handler. The category allow-list and status allow-list appear only here, making them invisible to the service and model layers.
Recommendation: Extract validation and domain logic into dedicated service functions. Controllers should only parse the request, call a service, and serialize the response (under 10 lines each).

### [CRITICAL] Dangerous Admin Endpoint — Arbitrary SQL Execution
File: app.py:59-78
Description: The `POST /admin/query` endpoint (`executar_query()`, lines 59-78) reads the `"sql"` field from the request body and passes it verbatim to `cursor.execute(query)` with no authentication, no input sanitization, and no allow-list. Any HTTP client can execute any SQL statement — including `DROP TABLE`, `UPDATE usuarios SET tipo='admin' WHERE id=<n>`, or SQLite's `ATTACH DATABASE` for file access. A second unauthenticated endpoint, `POST /admin/reset-db` (lines 47-57), deletes every row in every table with a single request.
Impact: Complete database compromise with one unauthenticated HTTP request. In SQLite environments this can extend to reading arbitrary files from the server via `ATTACH`.
Recommendation: Delete both endpoints. If constrained admin queries are genuinely required, implement an authenticated, allow-listed set of named report endpoints as shown in PB-04.

### [CRITICAL] Passwords Stored in Plaintext
File: models.py:105-131
Description: `login_usuario()` (lines 105-120) compares passwords by embedding them directly in a SQL query string — meaning they are stored and compared as plaintext. `criar_usuario()` (lines 122-131) inserts the raw `senha` parameter from the request with no hashing. The seed data in `database.py` (lines 75-82) likewise stores `"admin123"`, `"123456"`, and `"senha123"` as cleartext.
Impact: A single SQL dump or injection attack exposes every user's real password, which users likely reuse on other services.
Recommendation: Apply `bcrypt` or `argon2` hashing at `criar_usuario()` write time and verify with the library's constant-time compare at login. Never store or log plaintext passwords.

### [HIGH] Business Logic Embedded in Route Handlers
File: controllers.py:24-255
Description: Three handlers embed non-trivial domain rules: `criar_produto()` (lines 24-62) enforces a hardcoded category allow-list (`["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]`) and field-level validations that belong in a service or validator; `criar_pedido()` (lines 188-220) directly prints EMAIL, SMS, and PUSH notification strings inline after inserting the order; `atualizar_status_pedido()` (lines 237-255) encodes status-transition notifications inside the handler (`if novo_status == "aprovado": print(...)`). The valid-status allow-list also lives only here (line 242).
Impact: Adding a new product category or a real notification channel requires touching HTTP handlers. Business rules cannot be reused or tested independently.
Recommendation: Extract validation into a `ProductValidator`, notifications into a `NotificationService`, and status-transition logic into an `OrderService` following playbook PB-06.

### [HIGH] Global Mutable Database Connection
File: database.py:4-10
Description: `db_connection = None` is a module-level variable (line 4) mutated by `get_db()` (lines 7-86) on first call with no thread safety (`check_same_thread=False` only suppresses the sqlite3 warning, it does not make the connection thread-safe). A single connection is reused across all requests and all threads for the lifetime of the process.
Impact: Concurrent requests share one SQLite connection, producing race conditions, cursor interference, and potential data corruption under any multi-threaded or multi-process deployment.
Recommendation: Use Flask's `g` object and `@app.teardown_appcontext` to create a per-request connection, or adopt SQLAlchemy with a proper connection pool.

### [HIGH] Missing Environment Configuration
File: app.py:7-88
Description: Three configuration values are hardcoded literals with no environment override: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` (line 7), `app.config["DEBUG"] = True` (line 8), and `app.run(host="0.0.0.0", port=5000, debug=True)` (line 88). A `.env` file exists at the project root with the correct variable names (`SECRET_KEY`, `FLASK_ENV`, `PORT`) but is never loaded — `python-dotenv` is not in `requirements.txt` and `load_dotenv()` is never called.
Impact: Every environment (development, staging, production) runs with the same secret key and debug mode on. Changing any value requires a code edit and redeployment.
Recommendation: Add `python-dotenv` to `requirements.txt`, call `load_dotenv()` at startup, and read every runtime parameter from `os.getenv()` with safe defaults.

### [MEDIUM] N+1 Query Pattern — Orders Fetching Items and Products
File: models.py:171-233
Description: Both `get_pedidos_usuario()` (lines 171-201) and `get_todos_pedidos()` (lines 203-233) implement the same triple-loop query pattern: one outer `SELECT * FROM pedidos` is followed by a `SELECT * FROM itens_pedido WHERE pedido_id = ?` for each pedido, and then a `SELECT nome FROM produtos WHERE id = ?` for each item. For a list of 100 orders with 5 items each, this issues 100 x 5 + 100 + 1 = 601 queries.
Impact: Response time degrades linearly with order count. Under load, the SQLite connection is held across hundreds of synchronous round-trips per request.
Recommendation: Replace with a single JOIN across `pedidos`, `itens_pedido`, and `produtos`, then reshape the flat rows into the nested dict structure in Python.

### [MEDIUM] Bare / Generic Exception Handling
File: controllers.py:6-292
Description: Every handler function in `controllers.py` wraps its body in `except Exception as e:` (13 occurrences) and returns `jsonify({"erro": str(e)}), 500`. No specific exception type is caught, no structured logging is performed (only `print()` calls in a few handlers), and the raw exception message is returned to the HTTP client — which can reveal internal paths, table names, and SQL errors.
Impact: Debugging is hard because all errors look identical. `KeyboardInterrupt` and `SystemExit` are silenced. SQL error messages returned to clients aid attackers.
Recommendation: Catch specific exception types (`ValueError` for input errors, `sqlite3.Error` for DB errors). Log with `logging.exception()`. Register a Flask error handler for 500 responses that returns a generic message and logs internally.

### [MEDIUM] Debug Mode Always Enabled
File: app.py:8
Description: `app.config["DEBUG"] = True` is set unconditionally at module load (line 8), and `app.run(..., debug=True)` repeats the flag at line 88. Flask's Werkzeug interactive debugger is reachable from any request that triggers an unhandled exception, exposing an in-browser Python REPL to anyone who can reach the server.
Impact: Any unauthenticated user who triggers a 500 error gets an interactive Python shell with the server's full environment, file system, and process memory.
Recommendation: Gate on environment: `DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'`.

### [MEDIUM] Duplicated Query Logic — Order Retrieval
File: models.py:171-233
Description: `get_pedidos_usuario()` (lines 171-201) and `get_todos_pedidos()` (lines 203-233) are structurally identical: both execute an outer orders query, then iterate with the same nested cursor2/cursor3 pattern to assemble the `"itens"` list. Approximately 25 lines of logic are copy-pasted between the two, differing only in the WHERE clause of the outer query.
Impact: A bug fix to item-fetching logic (e.g., handling a NULL product) must be applied in two places; in practice one copy will be missed.
Recommendation: Extract the item-fetching and dict-assembly into a private `_build_pedido_dict(row)` helper and call it from both functions. Then consolidate the duplicated N+1 pattern with the JOIN fix from AP-10.

### [LOW] Magic Numbers — Tiered Discount Thresholds
File: models.py:255-261
Description: `relatorio_vendas()` compares `faturamento` against the numeric literals `10000`, `5000`, and `1000`, and multiplies by `0.1`, `0.05`, and `0.02` with no named constant or comment explaining what each threshold represents. The discount percentages (10%, 5%, 2%) are invisible from the literal values.
Impact: A business rule change (e.g., "raise the top-tier threshold to 15,000") requires finding the literal in context rather than updating a named constant.
Recommendation: Define `DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]` in a constants module and iterate over it in `relatorio_vendas()`.

================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
