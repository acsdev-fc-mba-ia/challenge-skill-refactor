================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code
Date:    2026-05-17

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 6 | LOW: 2
Total findings: 14

## Findings

### [CRITICAL] Hardcoded Secrets / Credentials — SECRET_KEY
File: app.py:13
Description: `app.config['SECRET_KEY']` is assigned the literal string
  `'super-secret-key-123'` directly in app.py. The value is committed to
  version control and visible to anyone with repository access.
Impact: Any user with read access to the repository can forge session cookies
  and impersonate any authenticated user.
Recommendation: Move to `.env` as `SECRET_KEY=<generated value>` and load
  with `os.getenv('SECRET_KEY')`; raise `RuntimeError` if absent.

### [CRITICAL] Hardcoded Secrets / Credentials — SMTP Password
File: services/notification_service.py:9-10
Description: `NotificationService.__init__` assigns `self.email_user =
  'taskmanager@gmail.com'` and `self.email_password = 'senha123'` as
  class-level literals. Both values are committed to version control.
Impact: The Gmail account can be taken over and abused for spam or phishing;
  rotating the password requires a code change and a new deployment.
Recommendation: Load both from environment variables
  (`EMAIL_USER`, `EMAIL_PASSWORD`) via `os.getenv()` and provide them
  in `.env.example`.

### [CRITICAL] Weak / Custom Cryptography — MD5 Password Hashing
File: models/user.py:28-32
Description: `User.set_password()` and `User.check_password()` use
  `hashlib.md5(pwd.encode()).hexdigest()` to store and verify passwords.
  MD5 is an unsalted, fast hash — not a password-hashing primitive.
Impact: The entire password database can be reversed via rainbow tables or
  GPU brute-force in minutes; no per-user salt prevents pre-computation attacks.
Recommendation: Replace with `bcrypt` or `argon2-cffi`:
  `from passlib.hash import bcrypt; self.password = bcrypt.hash(plain)`.

### [HIGH] Business Logic Embedded in Route Handlers — get_tasks()
File: routes/task_routes.py:11-63
Description: `get_tasks()` performs manual dictionary construction for every
  task field (lines 17-28), an inline overdue date calculation (lines 30-39),
  and per-task `User.query.get()` / `Category.query.get()` lookups (lines
  41-57) — all inside the route handler. The handler is 52 lines long with
  no service delegation.
Impact: Overdue logic cannot be unit-tested without an HTTP context; the same
  calculation is duplicated in at least four other locations, so a rule change
  must be applied in all copies.
Recommendation: Extract task serialization and overdue computation into
  `TaskService.get_all()` in `services/task_service.py`; reduce the handler
  to parse → call service → `jsonify`.

### [HIGH] Business Logic Embedded in Route Handlers — summary_report()
File: routes/report_routes.py:13-101
Description: `summary_report()` is an 88-line handler that computes five
  separate status counts (lines 19-22), five priority counts (lines 24-28),
  an overdue list with `days_overdue` arithmetic (lines 30-43), a 7-day
  activity window query (lines 45-51), and a full per-user productivity loop
  (lines 53-68) — all inline without a service layer.
Impact: Report logic is untestable in isolation; the overdue block is a
  near-verbatim copy of the one in `task_routes.py:30-39`, so any business
  rule change must be applied in multiple files.
Recommendation: Extract report aggregation into `ReportService.summary()`;
  reduce handler to a single service call and `jsonify`.

### [HIGH] Missing Environment Configuration
File: app.py:11-13, 34
Description: Three literal values are set unconditionally: `SQLALCHEMY_
  DATABASE_URI = 'sqlite:///tasks.db'` (line 11), `SECRET_KEY = 'super-
  secret-key-123'` (line 13), and `app.run(debug=True, host='0.0.0.0',
  port=5000)` (line 34). `python-dotenv` is listed in `requirements.txt`
  but is never imported or called anywhere in the project.
Impact: Configuration cannot differ between development and production
  without editing source code; debug=True in production exposes the
  Werkzeug interactive debugger via any unhandled exception.
Recommendation: Create `config/settings.py` that calls `load_dotenv()` and
  reads all values via `os.getenv()`; reference that module from `app.py`;
  provide `.env.example` with placeholder values.

### [MEDIUM] N+1 Query Pattern — get_tasks()
File: routes/task_routes.py:41-57
Description: `get_tasks()` calls `Task.query.all()` (line 14), then inside
  the loop calls `User.query.get(t.user_id)` (line 42) and
  `Category.query.get(t.category_id)` (line 51) for every task — producing
  2N+1 queries for N tasks.
Impact: Retrieving 100 tasks issues 201 database queries; under modest load
  this saturates connection pool capacity.
Recommendation: Add `joinedload` options:
  `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`
  and access `t.user` / `t.category` directly inside the loop.

### [MEDIUM] N+1 Query Pattern — summary_report() user productivity loop
File: routes/report_routes.py:53-68
Description: `summary_report()` calls `User.query.all()` (line 53) then,
  inside the loop, issues `Task.query.filter_by(user_id=u.id).all()` (line
  56) for every user — one extra query per user.
Impact: With 50 users the report endpoint issues 51 queries; response time
  grows linearly with the user count.
Recommendation: Replace with a single aggregation query using
  `db.session.execute(select(Task.user_id, func.count()).group_by(Task.user_id))`
  or eager-load tasks on the User relationship with `joinedload(User.tasks)`.

### [MEDIUM] Bare / Generic Exception Handling
File: routes/task_routes.py:62, 137, 232; routes/user_routes.py:130, 149;
      routes/report_routes.py:187, 208, 222; utils/helpers.py:47, 49
Description: Multiple `except:` blocks with no exception type appear
  throughout the route files (e.g., `task_routes.py:62` inside `get_tasks()`,
  `task_routes.py:232` inside `delete_task()`, `user_routes.py:130` inside
  `update_user()`). These bare clauses catch `KeyboardInterrupt` and
  `SystemExit` as well as application errors.
Impact: Signal-based process shutdown is swallowed, making the server
  unresponsive to graceful stop; the root cause of every database error is
  silently discarded, making debugging require log correlation.
Recommendation: Replace `except:` with `except (ValueError, SQLAlchemyError)
  as e:`, roll back the session on DB errors, and log with
  `logger.exception(...)`.

### [MEDIUM] Debug / Verbose Mode Enabled by Default
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` hardcodes
  `debug=True` with no environment check; the Werkzeug interactive debugger
  is reachable from any network interface when this process runs.
Impact: An unauthenticated attacker who triggers any unhandled exception
  receives an interactive Python console that allows arbitrary code execution.
Recommendation: Replace with
  `debug = os.getenv('FLASK_ENV') == 'development'`
  loaded from `config/settings.py`.

### [MEDIUM] Duplicated Logic — Overdue Calculation
File: routes/task_routes.py:30-39, 71-80, 283-287;
      routes/user_routes.py:171-181; routes/report_routes.py:33-38, 132-135;
      models/task.py:51-61
Description: The overdue check (`if t.due_date < datetime.utcnow() and
  t.status not in ('done', 'cancelled')`) is copy-pasted across seven
  locations in four files. The model already has a correct `is_overdue()`
  method (models/task.py:50) but it is never called from any route.
Impact: A rule change (e.g., adding a grace period) must be applied in seven
  places; any missed copy produces inconsistent API responses.
Recommendation: Delete all inline overdue blocks and call `task.is_overdue()`
  everywhere; keep the single canonical implementation on the model.

### [MEDIUM] Deprecated API Usage — datetime.utcnow()
File: routes/task_routes.py:31, 72, 215, 285;
      routes/user_routes.py:172; routes/report_routes.py:35, 44, 46, 71, 133;
      models/task.py:15-16, 52; services/notification_service.py:36;
      utils/helpers.py:39
Description: `datetime.utcnow()` is used in 14 locations across the codebase.
  The method is soft-deprecated in Python 3.12 because it returns a naive
  (timezone-unaware) datetime, which silently compares incorrectly with
  timezone-aware values.
Impact: Comparisons between naive and aware datetimes will raise `TypeError`
  when the codebase is updated to use timezone-aware values; migrating Python
  will surface latent bugs.
Recommendation: Replace all occurrences with
  `datetime.now(timezone.utc)` (import `timezone` from `datetime`).

### [LOW] Magic Numbers and Magic Strings — Status and Role Literals
File: routes/task_routes.py:32-33, 110, 177;
      routes/user_routes.py:71, 119; routes/report_routes.py:120-123;
      models/task.py:39-40, 52-53
Description: Status strings `'pending'`, `'in_progress'`, `'done'`,
  `'cancelled'` and role strings `'user'`, `'admin'`, `'manager'` are
  scattered as raw literals across eight files. `utils/helpers.py:110-116`
  defines `VALID_STATUSES` and `VALID_ROLES` constants but they are never
  imported by any route.
Impact: Renaming a status value requires a fragile global search; a typo in
  any copy silently passes validation.
Recommendation: Promote to `enum.Enum` classes in `models/constants.py`;
  import and reference by name everywhere — use the already-defined constants
  from `utils/helpers.py` as a starting point.

### [LOW] Poor Naming Conventions — Single-Letter and Cryptic Variables
File: routes/task_routes.py:16, 267-268; routes/report_routes.py:24-28, 54
Description: Loop variables `t` (task_routes.py:16), `u` (report_routes.py:54),
  and priority counter aliases `p1`–`p5` (report_routes.py:24-28) are used
  in non-trivial handler bodies. Boolean `overdue` (task_routes.py:33)
  should be named `is_overdue` to follow the yes/no convention.
Impact: Contributors must trace the variable through several lines of code
  to understand its type and domain meaning.
Recommendation: Rename to descriptive identifiers: `task`, `user`, and
  `priority_1_count`; rename boolean to `is_overdue`.

================================
