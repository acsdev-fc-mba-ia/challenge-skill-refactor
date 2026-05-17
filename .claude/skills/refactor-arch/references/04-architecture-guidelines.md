# Architecture Guidelines — MVC Target Pattern

These guidelines define the target structure for Phase 3 refactoring. They are stack-agnostic: directory names use snake_case for readability but the adapter for each stack (`stack-adapters/<stack>.md § Layout`) gives the idiomatic naming, file extensions, and concrete examples for that language.

The goal is not to copy a structure — it is to enforce the **responsibilities and rules** described below. Two valid MVC implementations in different languages may look superficially different but obey the same separation.

---

## Target Layout (conceptual)

```
<project-root>/
├── <environment template>           # e.g. .env.example — placeholder values, no secrets
├── <composition root>               # Minimal entry point: wires layers together
├── <database bootstrap>             # ORM / connection initialization
├── <dependency manifest>            # requirements.txt / package.json / go.mod / ...
│
├── config/                          # Loads env vars; exports typed constants
├── models/                          # One file per domain entity — ORM / data definition
├── services/                        # Business logic and orchestration across models
├── controllers/                     # HTTP request parsing → service call → response
├── routes/                          # URL ↔ controller mapping only
└── middleware/                      # Cross-cutting concerns (errors, auth, validation)
```

The stack adapter shows the language-appropriate file names, extensions, and import idioms for each of these directories.

---

## Layer Responsibilities

### `config/`
- **Responsibility:** Read environment variables once at startup and expose them as typed, named constants.
- **May:** Provide safe defaults for development.
- **Must not:** Import from other application layers. Open database connections. Define routes. Contain business logic. Have side effects beyond reading env vars.
- **Typical contents:** values like `SECRET_KEY`, `DATABASE_URL`, `SMTP_HOST`, `PORT`, `DEBUG`, `ALLOWED_ORIGINS`.

### `models/`
- **Responsibility:** Represent domain entities and their persistence. Provide simple, data-bound methods (`to_dict`, `is_overdue`, etc.).
- **May:** Define relationships, validation constraints, lightweight derived properties.
- **Must not:** Import from the HTTP layer (`request`, `response`, status codes). Send email, call payment gateways, generate reports. Contain business rules that span multiple entities.
- **One file per entity.** Never combine two entities in the same file.

### `services/`
- **Responsibility:** Implement business logic and orchestrate operations across multiple models.
- **May:** Import models. Import other services. Send notifications, call external APIs, run aggregations, enforce domain invariants.
- **Must not:** Import HTTP types or serialize to response formats. Touch the request lifecycle.
- **Test surface:** a service should be testable by calling its methods directly, without spinning up an HTTP server.

### `controllers/`
- **Responsibility:** Translate between HTTP and the service layer.
- **May:** Parse request data, call the appropriate service, serialize the result, map service exceptions to HTTP status codes.
- **Must not:** Contain domain logic, perform calculations, access the database directly, send email, do crypto.
- **Shape:** controllers are thin. If a controller has more than a handful of lines past parse-call-serialize, the extra logic belongs in a service.

### `routes/`
- **Responsibility:** Map URL + HTTP method to a controller function.
- **Must not:** Contain `if` statements, logic, or imports from models or services.
- **Shape:** one line per route, declaring the binding. Nothing else.

### `middleware/`
- **Responsibility:** Cross-cutting concerns that apply uniformly across many routes.
- **Typical members:**
  - **Error handler** — catches unhandled exceptions, formats a consistent error response, logs the cause.
  - **Auth** — verifies tokens / sessions, attaches the authenticated subject to the request context.
  - **Validation** — checks request bodies against a schema before they reach the controller.

### Composition root (entry point)
- **Responsibility:** Create the app, register middleware, register routes, initialize the database, start the server.
- **Size budget:** 20–40 lines. Anything longer indicates that another layer is leaking into it.
- **Must not:** Define route handlers, contain business logic, declare models, or hold configuration literals.

---

## Non-Negotiable Rules for Phase 3

These rules apply regardless of stack. The adapter shows *how* to satisfy each one in the target language; this file shows *what* must be true.

1. **No hardcoded secrets remain.** Every credential, key, or environment-specific value is loaded from the environment via `config/`.
2. **Routes do not contain business logic.** Domain rules live in services.
3. **Controllers do not access the database directly.** Persistence goes through models or services.
4. **A centralized error handler exists.** No silent exception swallowing anywhere in the codebase.
5. **The composition root is minimal.** It only wires things together.
6. **All original endpoints still work.** API consumers must not need to change. The endpoint inventory from Phase 1 is the contract.
7. **No business logic is duplicated across layers.** Each domain rule has exactly one home (usually a model method or service function).
8. **The `.env.example` lists every variable the app reads.** Placeholder values only — never real secrets.

---

## Stack-Specific Adaptations

The shape of MVC bends to the language. Examples — without code — of how the same responsibilities map to common stacks:

- **Python / Flask:** routes use `Blueprint`s; controllers are functions, not classes; models inherit from `db.Model` (SQLAlchemy); the composition root is an app factory.
- **Node.js / Express:** routes use `express.Router()` instances; controllers export handler functions; models can be ORM classes (Sequelize, Prisma) or plain classes wrapping queries; the composition root mounts routers on the app.
- **Java / Spring:** controllers are classes annotated `@RestController`; routes are method-level `@RequestMapping`; services are `@Service` beans; models are JPA entities; configuration uses `application.yml` + `@ConfigurationProperties`.
- **Go / Gin or net/http:** controllers are handler functions registered on a router; services are interfaces with concrete implementations; models are plain structs; configuration loaded via a `config` package.
- **Ruby / Rails:** the framework already enforces this structure — refactoring means moving fat-controller logic into service objects under `app/services/`.

For the active stack, see `stack-adapters/<stack>.md § Layout` for the concrete file/directory mapping, idiomatic naming, and worked examples per layer.
