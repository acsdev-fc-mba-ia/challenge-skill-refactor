# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **challenge-skill-refactor** project: an educational challenge for creating an AI-driven Skill that performs automated architectural refactoring and code quality audits. The challenge involves analyzing three legacy backend projects with intentional code smells, generating audit reports, and refactoring them to the MVC pattern.

The repository contains three target projects at different maturity levels:
- **code-smells-project**: Python/Flask e-commerce API (monolithic, ~780 LOC)
- **ecommerce-api-legacy**: Node.js/Express LMS API (~180 LOC, tightly coupled)
- **task-manager-api**: Python/Flask task manager (~900 LOC, partially organized)

## Architecture & Structure

### Root Organization

```
├── README.md                          # Main challenge specification and requirements
├── .gitignore                         # Standard (node_modules, __pycache__, .venv, *.db)
├── code-smells-project/               # Python/Flask — E-commerce (fully monolithic)
├── ecommerce-api-legacy/              # Node.js/Express — LMS API (tightly coupled)
└── task-manager-api/                  # Python/Flask — Task Manager (layered but flawed)
```

### Project-Specific Structures

#### 1. code-smells-project (Python/Flask Monolith)

Most tightly coupled of the three. All logic resides in 4 files without separation of concerns:

- **app.py** (88 LOC): Flask app setup + direct endpoint handlers for admin operations (database reset, raw SQL execution)
- **controllers.py** (292 LOC): Business logic and HTTP validation in one layer (no separation between request handling and domain logic)
- **models.py** (314 LOC): SQL queries mixed with data transformation; no ORM, raw string concatenation for queries
- **database.py** (86 LOC): Connection initialization and schema creation; seeded with sample e-commerce data on first boot
- **requirements.txt**: Flask 3.1.1, flask-cors 5.0.1

Stack: SQLite in-file (loja.db), runs on port 5000

#### 2. ecommerce-api-legacy (Node.js/Express)

LMS platform with integrated checkout. Single AppManager class handles all concerns:

- **src/app.js** (14 LOC): Express setup, delegates to AppManager
- **src/AppManager.js** (141 LOC): Database initialization, all route handlers (checkout, financial reports), business logic, and data processing in one class
- **src/utils.js** (25 LOC): Configuration (hardcoded credentials), caching mechanism, weak crypto, revenue tracking
- **api.http**: Example requests for testing
- **package.json**: Express 4.18.2, sqlite3 5.1.6

Stack: SQLite in-memory, runs on port 3000

#### 3. task-manager-api (Python/Flask Partially Layered)

Most organized of the three but still contains architectural violations and security issues:

- **app.py** (35 LOC): Flask setup with blueprint registration, hardcoded SECRET_KEY
- **database.py** (4 LOC): SQLAlchemy instance initialization
- **models/** (3 models, ~120 LOC): Task, User, Category using SQLAlchemy ORM
- **routes/** (3 blueprints, ~730 LOC): task_routes, user_routes, report_routes with business logic embedded
- **services/** (1 service, 48 LOC): NotificationService with hardcoded SMTP credentials
- **utils/** (1 helper, unknown LOC): Helper functions
- **seed.py**: Database seeding script
- **requirements.txt**: Flask 3.0.0, flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0, python-dotenv 1.0.0

Stack: SQLite (tasks.db), runs on port 5000

## Severity Classification System

The challenge defines a standardized severity framework for code quality findings:

- **CRITICAL**: Architectural failures or security exposures (hardcoded credentials, SQL injection vulnerabilities, "God Classes", missing MVC separation)
- **HIGH**: Strong MVC/SOLID violations impacting maintainability (business logic trapped in controllers, tight coupling, global mutable state)
- **MEDIUM**: Standardization issues, code duplication, moderate performance problems (N+1 queries, improper middleware usage, missing validation)
- **LOW**: Readability improvements, naming conventions, magic numbers

## Common Development Tasks

### Running Individual Projects

**code-smells-project:**
```bash
cd code-smells-project
pip install -r requirements.txt
python app.py
# Accessible at http://172.0.0.1:5000
```

**ecommerce-api-legacy:**
```bash
cd ecommerce-api-legacy
npm install
npm start
# Accessible at http://172.0.0.1:3000
# In-memory database auto-populated on startup
```

**task-manager-api:**
```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py                    # Must run before first boot to populate test data
python app.py
# Accessible at http://172.0.0.1:5000
```

### Key Endpoints by Project

**code-smells-project** (E-commerce):
- GET `/produtos`, POST `/produtos`, GET/PUT/DELETE `/produtos/<id>`
- GET `/usuarios`, POST `/usuarios`, GET `/usuarios/<id>`
- POST `/pedidos`, GET `/pedidos`, GET `/pedidos/usuario/<usuario_id>`, PUT `/pedidos/<id>/status`
- GET `/relatorios/vendas`
- POST `/admin/reset-db`, POST `/admin/query` (dangerous direct SQL execution)

**ecommerce-api-legacy** (LMS):
- POST `/api/checkout` (course enrollment + payment)
- GET `/api/admin/financial-report`

**task-manager-api** (Task Manager):
- GET/POST/PUT/DELETE `/tasks`
- GET/POST/PUT/DELETE `/users`
- GET/POST `/reports`

### Validation & Testing Strategy

After refactoring, validation requires:
1. **Boot validation**: Application starts without errors
2. **Endpoint validation**: All original endpoints respond correctly (status codes, data structure)
3. **No anti-patterns remaining**: Refactored code passes the same audit rules
4. **Database integrity**: Original test data loads correctly

No formal test suite exists in any project; validation is manual endpoint testing via CLI or api.http.

## Key Architectural Issues to Understand

These are intentional problems baked into the projects for the refactoring challenge:

### code-smells-project Issues

1. **SQL Injection via String Concatenation** (CRITICAL, models.py): Raw SQL built with `+` operators (e.g., `"SELECT * FROM productos WHERE id = " + str(id)`)
2. **Hardcoded Credentials** (CRITICAL, app.py:7): `SECRET_KEY = "minha-chave-super-secreta-123"`
3. **Dangerous Admin Endpoints** (CRITICAL, app.py:59-78): Direct SQL execution endpoint at `/admin/query` accepts arbitrary queries
4. **God Class Pattern** (CRITICAL, models.py): All business logic, data access, and transformations in one file
5. **Missing Input Validation** (HIGH, controllers.py): Some validations exist but inconsistently applied
6. **Mixing Concerns** (HIGH, controllers.py): HTTP handling + business logic + database orchestration in same functions
7. **No ORM** (HIGH, database.py): Manual schema management, raw SQL across multiple files
8. **Debug Mode in Production** (MEDIUM, app.py:8): `DEBUG = True` set explicitly
9. **Weak Error Handling** (MEDIUM, controllers.py): Generic exception handling with no logging strategy

### ecommerce-api-legacy Issues

1. **Monolithic Class** (CRITICAL, AppManager.js): Single 141-line class handles DB, routes, business logic, crypto, and reporting
2. **Hardcoded Config** (CRITICAL, utils.js:2-4): Database credentials, payment gateway key, and SMTP user exposed
3. **Weak Cryptography** (CRITICAL, utils.js:17-23): Password "hashing" is base64 encoding repeated 10,000 times, not cryptographic
4. **SQL Injection Risk** (HIGH, AppManager.js): Uses parameterized queries correctly, but design makes it fragile for extension
5. **Global Mutable State** (HIGH, utils.js:9-10): `globalCache` and `totalRevenue` as module-level variables
6. **Callback Hell** (HIGH, AppManager.js:40-77): Deeply nested async callbacks making code hard to follow
7. **No Request Validation** (MEDIUM, AppManager.js:28-34): Minimal input validation on checkout endpoint
8. **Race Conditions** (MEDIUM, AppManager.js:86-98): Sequential callback counting for async queries can lose increments

### task-manager-api Issues

1. **Hardcoded Credentials** (CRITICAL, notification_service.py:9-10): SMTP password hardcoded; no .env usage despite python-dotenv in requirements
2. **Missing Environment Configuration** (HIGH, app.py:13): SECRET_KEY hardcoded; should be loaded from .env
3. **Business Logic in Routes** (HIGH, routes/task_routes.py): Complex data transformation and overdue calculation duplicated across GET /tasks and GET /tasks/<id>
4. **N+1 Query Pattern** (MEDIUM, routes/task_routes.py:41-57): For each task, queries User and Category separately instead of eager loading
5. **Bare Exception Handling** (MEDIUM, routes/task_routes.py:62): `except:` catches everything including KeyboardInterrupt
6. **Code Duplication** (MEDIUM, routes/task_routes.py vs models/task.py): Overdue logic exists in both route handler and model method

## MVC Refactoring Target

All projects should be refactored to this structure (adapted to language/framework):

```
src/
├── config/                    # Environment-based configuration
│   └── settings.py           # Load from .env, expose as constants
├── models/                    # Data models (ORM entities or plain objects)
│   ├── product.py
│   ├── user.py
│   └── order.py
├── controllers/               # Request routing and orchestration
│   ├── product_controller.py
│   ├── user_controller.py
│   └── order_controller.py
├── views/ or routes/          # HTTP endpoint definitions (separation of routing)
│   └── routes.py
├── services/                  # Business logic layer
│   ├── product_service.py
│   ├── user_service.py
│   └── order_service.py
├── middleware/                # Cross-cutting concerns
│   ├── error_handler.py
│   ├── auth.py
│   └── validation.py
├── database.py               # ORM initialization, connection
└── app.py                    # Application entry point (minimal)
```

Key principles:
- Controllers handle HTTP (requests/responses), not business logic
- Services contain domain logic and orchestration
- Models represent entities; database interaction through ORM
- No hardcoded configuration; all from environment
- Centralized error handling
- Clear entry point with dependency injection

## Skill Development Notes

### Deliverable Structure

The skill lives **inside each project directory** at `.claude/skills/refactor-arch/`. The root `z_reports/` directory holds audit outputs:

```
challenge-skill-refactor/
├── code-smells-project/.claude/skills/refactor-arch/   # Primary skill location
├── ecommerce-api-legacy/.claude/skills/refactor-arch/  # Copy of skill
├── task-manager-api/.claude/skills/refactor-arch/      # Copy of skill
└── z_reports/
    ├── audit-project-1.md    # Phase 2 output for code-smells-project
    ├── audit-project-2.md    # Phase 2 output for ecommerce-api-legacy
    └── audit-project-3.md    # Phase 2 output for task-manager-api
```

### Skill File Requirements

Each `.claude/skills/refactor-arch/` folder must contain `SKILL.md` plus reference Markdown files covering these five knowledge areas:

| Area | Content |
|---|---|
| Project analysis | Heuristics for detecting language, framework, database, architecture |
| Anti-pattern catalog | ≥8 anti-patterns with detection signals and severity; must include deprecated API detection |
| Report template | Standardized Phase 2 audit report format with file:line references |
| Architecture guidelines | MVC target pattern — layer responsibilities for Models, Views/Routes, Controllers |
| Refactoring playbook | ≥8 before/after code transformation patterns, one per anti-pattern |

### Invocation

```bash
cd <project-dir>
claude "/refactor-arch"
```

### Key Constraints

- **Agnosticism requirement**: Must work across Python/Flask and Node.js/Express without stack-specific branching in SKILL.md
- **Detection heuristics**: Infer stack from `package.json`/`requirements.txt`, framework imports, existing directory layout
- **Report template**: Each finding must cite exact file and line range
- **Phase 2 user confirmation**: Mandatory pause before Phase 3 — skill must not modify any file without explicit approval
- **Phase 3 validation**: Boot the application and hit endpoints to confirm they respond correctly after refactoring

### Acceptance Criteria (all 3 projects)

| Criterion | Requirement |
|---|---|
| Phase 1 detects stack correctly | Mandatory |
| Phase 2 finds ≥5 findings | Mandatory |
| Phase 2 includes ≥1 CRITICAL or HIGH | Mandatory |
| Phase 3 app works after refactoring | Mandatory |

The README.md in the project root contains the full specification, acceptance criteria, and required README sections for the submission.