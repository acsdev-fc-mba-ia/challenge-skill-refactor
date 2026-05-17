================================
PHASE 3: REFACTORING COMPLETE
================================

## New Project Structure

task-manager-api/
├── .env.example                          ← NEW: all env vars with placeholder values
├── app.py                                ← UPDATED: minimal composition root (~35 LOC)
├── database.py                           ← unchanged
├── requirements.txt                      ← unchanged
├── seed.py                               ← UPDATED: datetime.utcnow() → now(timezone.utc)
├── config/
│   ├── __init__.py
│   └── settings.py                       ← NEW: load_dotenv() + all typed constants
├── models/
│   ├── __init__.py
│   ├── category.py                       ← UPDATED: datetime.utcnow() → now(timezone.utc)
│   ├── task.py                           ← UPDATED: datetime.now(tz), canonical is_overdue()
│   └── user.py                           ← UPDATED: MD5 → werkzeug PBKDF2, no pwd in to_dict
├── services/
│   ├── __init__.py
│   ├── exceptions.py                     ← NEW: ConflictError, AuthenticationError
│   ├── category_service.py               ← NEW: CategoryService business logic
│   ├── notification_service.py           ← UPDATED: hardcoded creds → config.settings
│   ├── report_service.py                 ← NEW: ReportService (extracted from report_routes)
│   ├── task_service.py                   ← NEW: TaskService (extracted from task_routes)
│   └── user_service.py                   ← NEW: UserService (extracted from user_routes)
├── controllers/
│   ├── __init__.py
│   ├── category_controller.py            ← NEW: parse → service → jsonify
│   ├── report_controller.py              ← NEW: parse → service → jsonify
│   ├── task_controller.py                ← NEW: parse → service → jsonify
│   └── user_controller.py               ← NEW: parse → service → jsonify
├── routes/
│   ├── __init__.py
│   ├── category_routes.py                ← NEW: Blueprint /categories/* (1 line per route)
│   ├── report_routes.py                  ← UPDATED: thin, delegates to report_controller
│   ├── task_routes.py                    ← UPDATED: thin, delegates to task_controller
│   └── user_routes.py                    ← UPDATED: thin, delegates to user_controller
├── middleware/
│   ├── __init__.py
│   └── error_handler.py                  ← NEW: centralized 404/405/500 handlers
└── utils/
    ├── __init__.py
    └── helpers.py                        ← unchanged (constants referenced but not migrated)

## Fixes Applied

| Anti-Pattern | Playbook | Fix |
|---|---|---|
| Hardcoded SECRET_KEY (app.py:13) | PB-01 | Moved to config/settings.py via os.getenv() |
| Hardcoded SMTP credentials (notification_service.py:9-10) | PB-01 | Moved to config/settings.py; loaded from env |
| MD5 password hashing (models/user.py:28-32) | PB-05 | Replaced with werkzeug.security PBKDF2 (generate_password_hash / check_password_hash) |
| Business logic in get_tasks() (task_routes.py:11-63) | PB-06 | Extracted to TaskService.get_all() with joinedload (fixes N+1 too) |
| Business logic in summary_report() (report_routes.py:13-101) | PB-06 | Extracted to ReportService.summary() with joinedload for user productivity |
| Missing environment configuration (app.py:11-34) | PB-01 | config/settings.py calls load_dotenv(); app.py imports constants; .env.example provided |
| N+1 in get_tasks() (task_routes.py:41-57) | PB-09 | joinedload(Task.user, Task.category) in TaskService.get_all() |
| N+1 in summary_report() user loop (report_routes.py:53-68) | PB-09 | joinedload(User.tasks) in ReportService.summary() |
| Bare except: handlers (10 locations) | PB-10 | Specific except (ValueError, SQLAlchemyError, LookupError); centralized error_handler.py |
| Debug mode unconditional (app.py:34) | PB-01 | debug=DEBUG loaded from FLASK_ENV env var |
| Duplicated overdue logic (7 locations) | PB-12 | All sites replaced with task.is_overdue(); canonical stays in models/task.py |
| datetime.utcnow() (14 locations) | PB-11 | Replaced with datetime.now(timezone.utc) + .replace(tzinfo=timezone.utc) for comparisons |
| Magic status/role strings | PB-13 | Centralized in VALID_STATUSES / VALID_ROLES constants in each service |
| Single-letter variables (t, u, p1-p5) | PB-14 | Renamed to task, user, priority_counts in all services and controllers |

## Validation

  ✓ GET / → 200 OK {"message": "Task Manager API"}
  ✓ GET /health → 200 OK {"status": "ok"}
  ✓ POST /login (valid credentials) → 200 OK {"message": "Login realizado com sucesso"}
  ✓ POST /login (invalid credentials) → 401 Unauthorized
  ✓ GET /users → 200 OK
  ✓ GET /users/1 → 200 OK
  ✓ GET /users/9999 → 404 Not Found
  ✓ POST /users (full payload) → 201 Created
  ✓ POST /users (duplicate email) → 409 Conflict
  ✓ POST /users (invalid role) → 400 Bad Request
  ✓ PUT /users/1 → 200 OK
  ✓ GET /users/1/tasks → 200 OK
  ✓ DELETE /users/3 → 200 OK
  ✓ GET /tasks → 200 OK
  ✓ GET /tasks/1 → 200 OK
  ✓ GET /tasks/9999 → 404 Not Found
  ✓ POST /tasks (full payload) → 201 Created
  ✓ POST /tasks (minimal) → 201 Created
  ✓ POST /tasks (title too short) → 400 Bad Request
  ✓ POST /tasks (invalid status) → 400 Bad Request
  ✓ POST /tasks (invalid priority) → 400 Bad Request
  ✓ PUT /tasks/1 (in_progress) → 200 OK
  ✓ PUT /tasks/1 (done) → 200 OK
  ✓ DELETE /tasks/5 → 200 OK
  ✓ GET /tasks/search?status=pending → 200 OK
  ✓ GET /tasks/search?priority=1 → 200 OK
  ✓ GET /tasks/search?status=pending&priority=1&user_id=1 → 200 OK
  ✓ GET /tasks/stats → 200 OK
  ✓ GET /categories → 200 OK
  ✓ POST /categories → 201 Created
  ✓ POST /categories (no name) → 400 Bad Request
  ✓ PUT /categories/1 → 200 OK
  ✓ DELETE /categories/4 → 200 OK
  ✓ GET /reports/summary → 200 OK
  ✓ GET /reports/user/1 → 200 OK
  ✓ GET /reports/user/9999 → 404 Not Found

## Environment Variables

  Created: .env.example
  Variables:
    SECRET_KEY         — Flask session signing key
    DATABASE_URL       — SQLAlchemy connection string (default: sqlite:///tasks.db)
    FLASK_ENV          — 'development' enables debug mode (default: production)
    PORT               — HTTP port (default: 5000)
    HOST               — Bind address (default: 0.0.0.0)
    EMAIL_HOST         — SMTP server hostname
    EMAIL_PORT         — SMTP port (default: 587)
    EMAIL_USER         — SMTP sender address
    EMAIL_PASSWORD     — SMTP authentication password

================================
