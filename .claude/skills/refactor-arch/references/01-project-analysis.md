# Project Analysis — Detection Heuristics

Use these heuristics during Phase 1 to detect the stack and map the current architecture. All heuristics here are language-agnostic. Stack-specific signals live in `stack-adapters/<stack>.md` and are loaded conditionally.

---

## 1. Language Detection

Check for manifest files in this priority order. The deepest manifest relative to the project root wins.

| File found | Language |
|---|---|
| `package.json` | Node.js / JavaScript / TypeScript |
| `requirements.txt` / `pyproject.toml` / `Pipfile` / `setup.py` | Python |
| `go.mod` | Go |
| `pom.xml` / `build.gradle` / `build.gradle.kts` | Java / Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `Cargo.toml` | Rust |
| `*.csproj` / `*.fsproj` / `*.sln` | .NET (C# / F#) |
| `mix.exs` | Elixir |

If no manifest is found, fall back to extension-counting in the source tree.

---

## 2. Framework Detection

Open the manifest and read the dependency list. Stack-specific mappings of `package → framework` live in the adapter for that language (`stack-adapters/<stack>.md § Framework Map`).

General rule: identify the package that owns the HTTP server / request routing, and read its declared version string. Examples of declaration formats:

- `package.json` — `"<package>": "<version>"` inside `dependencies`
- `requirements.txt` — `<package>==<version>` or `<package>>=<version>` per line
- `pyproject.toml` — `<package> = "<version>"` inside `[tool.poetry.dependencies]` or `[project] dependencies`
- `go.mod` — `require <module> <version>`
- `pom.xml` — `<dependency><artifactId>...</artifactId><version>...</version></dependency>`

If the adapter for the detected language is missing, record the framework name as observed and proceed with the agnostic catalog only.

---

## 3. Database Layer Detection

The data layer can be inferred from two independent signals — combine both:

**A. Dependency / import signals** (stack-specific — see adapter)
- ORMs and query builders are imported as packages. Each adapter lists the typical ORM/driver packages for its stack and the import patterns that flag them.

**B. Structural signals** (stack-agnostic)
- Files with extensions like `.db`, `.sqlite`, `.sqlite3` indicate SQLite.
- Plain SQL files (`schema.sql`, `migrations/*.sql`) indicate schema is managed manually or via a migration tool.
- Presence of a `migrations/`, `alembic/`, `prisma/`, `knexfile.*` directory indicates a migration framework.
- Source files containing `CREATE TABLE` strings indicate raw schema definition.
- Class definitions with attributes matching ORM idioms (column declarations, table-name attributes, model base classes) indicate ORM use.

If the application contains no database access at all, record `DB layer: none detected`.

---

## 4. Architecture Pattern Detection

Count files per top-level directory and cross-reference with these patterns. Architecture detection is purely structural — it does not depend on language.

### Fully Monolithic
- All logic concentrated in 1–4 files at the project root.
- No subdirectories for models, routes, or services.
- A single entry-point file handles routing + business logic + database access.

### Partially Layered
- Some directories exist (`models/`, `routes/`, `services/`, `controllers/`) but responsibilities bleed across layers.
- Business logic appears inside route/controller handlers.
- Data-access code appears outside `models/` (e.g., inside controllers).

### MVC / Clean Architecture
- Clear separation between data (`models/`), HTTP handling (`controllers/`), routing (`routes/`), business logic (`services/`).
- Entry point is minimal — it only wires components together.
- Configuration is loaded from environment variables, not literals.

### God Class / God File Signal
- A single source file > 200 LOC containing route definitions, database queries, business logic, and/or cryptography simultaneously.
- A single class whose responsibilities span more than one of: routing, persistence, domain logic, external integrations.
- Look at filenames suggesting centralization: `*Manager`, `*Helper`, `app.*`, `main.*`, `index.*` with disproportionate line counts.

---

## 5. Domain Inference

Do not guess the domain from a predefined list. Infer it from the **vocabulary** the project uses. Collect signals from:

- Route paths (the nouns used in URLs)
- Database table names and column names
- Model / class names
- Filenames of source modules
- Comments and docstrings near the entry point

Then describe the domain in **one sentence** using the dominant nouns observed, in the project's own language. Examples:

- Project uses `/products`, `/orders`, table `products` → "E-commerce API (products and orders)"
- Project uses `/tasks`, `/users`, `/categories`, `/reports` → "Task / project management API"
- Project uses `/courses`, `/enrollments`, `/payments` → "Education platform with paid enrollment"

If the project mixes two distinct vocabularies (e.g., `/courses` AND `/payments`), describe both and pick the dominant one as the primary domain.

---

## 6. Endpoint Inventory

If a `.http` / `.rest` / `requests.http` file is present at the project root or under `tests/`, parse it to extract the endpoint list:

- Lines starting with an HTTP verb (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) followed by a URL are endpoint definitions.
- Lines starting with `###` are section separators.
- Indented or following JSON blocks are request bodies.

If no `.http` file exists, fall back to scanning route declarations in the source code. The adapter for each stack lists the route-declaration idioms (decorator-based, method-based, config-file-based, etc.).

Build a table: `method | path | has body (yes/no) | source (api.http or source-file:line)`.

This table is used in Phase 3 validation to know exactly which endpoints to exercise.

---

## 7. Phase 1 Output Rules

- **DO NOT GUESS.** Only report what is directly observed in files.
- If a field cannot be determined, write `not detected` rather than inferring.
- The architecture description must be a single sentence capturing the most critical structural fact — e.g., "Single 141-line file holding DB initialization, routes, business logic and crypto."
- Source-file count must **exclude**: dependency directories (`node_modules/`, `.venv/`, `vendor/`, `target/`, `build/`, `dist/`), cache directories (`__pycache__/`, `.pytest_cache/`), version control (`.git/`), tool config (`.claude/`, `.idea/`, `.vscode/`), compiled output (`*.pyc`, `*.class`, `*.o`), and database files (`*.db`, `*.sqlite*`).
- If a stack adapter exists for the detected language, record `Adapter: <stack-adapters/python.md>` (or equivalent) in the Phase 1 output so subsequent phases know it was loaded. If no adapter exists, record `Adapter: none — using agnostic signals only` and proceed.
