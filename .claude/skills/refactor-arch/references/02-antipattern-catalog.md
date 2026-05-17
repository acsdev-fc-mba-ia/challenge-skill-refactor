# Anti-Pattern Catalog

Each anti-pattern is described in three blocks:

1. **Concept** — the abstract definition (language-independent).
2. **Semantic Signals** — what to look for, in concepts, not syntax.
3. **Stack-Specific Signals** — pointer to the matching section in `stack-adapters/<stack>.md § <AP-id>`.

If no stack adapter is loaded, **the Concept + Semantic Signals alone are sufficient to detect every anti-pattern** — they are written so an attentive reader can find the pattern in any language by reasoning, not by string-matching.

Apply every entry to every source file during Phase 2.

---

## CRITICAL

---

### AP-01 — Hardcoded Secrets / Credentials

**Severity:** CRITICAL

**Concept:** Any value that grants access to a protected resource (signing keys, passwords, API tokens, connection strings) is committed to source code as a literal, instead of being loaded from configuration external to the codebase.

**Semantic Signals:**
- A variable, constant, attribute, struct field, or configuration entry whose name contains any of: `secret`, `password`, `passwd`, `pwd`, `key`, `token`, `auth`, `credential`, `private`, `api_key`, `apikey`, `access_key`, `dsn`, `connection_string` — and the assigned value is a literal string (not a function call to an env/config reader).
- A connection URL containing inline credentials (e.g., `protocol://user:pass@host`).
- A literal that looks like a real-world key by format alone (long random-looking string, JWT, base64 blob assigned to a `*KEY` identifier).

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-01`

**Impact:** Credentials in version control are permanently exposed (git history retains deleted lines). Enables unauthorized access to databases, payment gateways, mail servers, and signing infrastructure.

**Recommended fix direction:** Move the value to an environment variable. Load via the language's environment-reading idiom. Commit a `.env.example` with placeholder values.

---

### AP-02 — SQL Injection via String Interpolation

**Severity:** CRITICAL

**Concept:** A SQL statement is constructed by mixing user-controlled data into the query string itself, rather than passing the data as a separate, parameterized argument to the database driver.

**Semantic Signals:**
- A SQL query whose final string is the result of concatenation, formatting, or template expansion — and at least one of the interpolated fragments originates (directly or indirectly) from a request input.
- A call to a database driver's "execute / query / run" function where the SQL argument is not a static literal.
- A query-building helper that returns a string assembled from inputs and is then passed verbatim to the driver.
- Inputs reaching the SQL string without passing through a known parameter-binding API.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-02`

**Impact:** Attackers can read, modify, or destroy any data the application has access to. Often escalates to full database compromise and arbitrary file read on the DB server.

**Recommended fix direction:** Use the driver's parameter-binding API (placeholders like `?`, `$1`, `:name`) or switch to an ORM. Inputs must never become part of the SQL string itself.

---

### AP-03 — God Class / God File

**Severity:** CRITICAL

**Concept:** A single file or class concentrates responsibilities that, in a properly layered design, would live in distinct modules — typically routing, persistence, business logic, and integrations all in one place.

**Semantic Signals:**
- A single source file > 200 LOC that simultaneously contains two or more of: route/endpoint declarations, database queries or ORM-model definitions, domain calculations, cryptographic operations, external-service calls (email, payments, HTTP), report generation.
- A single class whose method set spans setup (DB init), HTTP handling, business rules, and utility helpers.
- A filename suggesting centralization (`*Manager`, `*Helper`, `app.*`, `main.*`, `index.*`) with disproportionately high LOC compared to siblings.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-03`

**Impact:** Cannot be tested in isolation. Any change risks breaking unrelated functionality. Onboarding new developers is slow because intent is hidden inside size.

**Recommended fix direction:** Decompose into one module per responsibility, organized by MVC layer (see `04-architecture-guidelines.md`). One domain entity per file per layer.

---

### AP-04 — Dangerous Admin Endpoint (Arbitrary Code / SQL Execution)

**Severity:** CRITICAL

**Concept:** An HTTP endpoint accepts a payload that is interpreted as code or SQL by the server — handing remote execution to whoever can call the endpoint.

**Semantic Signals:**
- A route whose handler reads a field named like `query`, `sql`, `cmd`, `command`, `script`, `code`, `expr` from the request and forwards it to a code-evaluation or SQL-execution primitive.
- Any route described as "admin" or "debug" that runs caller-supplied strings through `eval`, `exec`, `Function()`, `runtime.exec`, or a database `execute()`.
- Direct exposure of an interactive shell, REPL, or query console through HTTP.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-04`

**Impact:** Complete server takeover with a single request. Attackers can read every secret, exfiltrate the database, or pivot into the host.

**Recommended fix direction:** Delete the endpoint entirely. If admin DB access is genuinely required, use a dedicated, authenticated tool out-of-band — never expose raw execution over HTTP. If a constrained subset is needed, implement a strict allow-list of named operations.

---

### AP-05 — Weak / Custom Cryptography

**Severity:** CRITICAL

**Concept:** Sensitive data (especially passwords) is protected using a non-cryptographic encoding, a broken algorithm, or a hand-rolled scheme instead of a standard, vetted primitive.

**Semantic Signals:**
- Password storage using an encoding function (base64, hex, URL-encoding) presented as "hashing", regardless of how many times it is repeated.
- Use of MD5 or SHA-1 for password storage (any unsalted, fast hash for passwords).
- Custom encryption based on XOR, character shifting, or other reversible-by-inspection schemes.
- Symmetric cipher usage without an explicit IV / nonce.
- Passwords stored without a per-user salt.
- "Encryption" implemented from scratch in application code rather than via a standard library.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-05`

**Impact:** The password database is trivially reversible. All user accounts can be compromised via rainbow tables or simple decoding.

**Recommended fix direction:** Replace with a standard password-hashing primitive (`bcrypt`, `argon2`, `scrypt`) provided by a vetted library. For symmetric encryption, use authenticated encryption (e.g., AES-GCM) with proper IV handling.

---

## HIGH

---

### AP-06 — Business Logic Embedded in Route / Controller Handlers

**Severity:** HIGH

**Concept:** Domain rules and calculations live inside HTTP handlers, mixing the responsibility of "speak HTTP" with the responsibility of "implement domain behavior".

**Semantic Signals:**
- A route handler whose body contains more than: request parsing, a single service call, and response serialization.
- Domain calculations performed inline in the handler: date arithmetic, price/tax/discount math, status-machine transitions, aggregation across multiple entities, conditional triggering of side-effects (email, payment).
- The same handler reaches into multiple persistence operations without delegating to a coordinating function.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-06`

**Impact:** Handlers cannot be tested without an HTTP context. The same rule gets reimplemented in every handler that needs it, producing inconsistencies. Violates single-responsibility and makes any refactor risky.

**Recommended fix direction:** Extract the logic into a service layer. Handlers become thin: parse request → call service → return response.

---

### AP-07 — Global Mutable State

**Severity:** HIGH

**Concept:** State that is shared across requests is held in module-level or class-level variables and mutated from request handlers, with no concurrency control or encapsulation.

**Semantic Signals:**
- A module-level (or static / class-level) variable that is **written** at request time, not just read.
- A "cache" object kept as a top-level binding and mutated inline from handlers.
- A running counter / total that is mutated across requests (`total += amount`, `count += 1`).
- Singleton-like state without an explicit, thread-safe wrapper around it.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-07`

**Impact:** Race conditions under concurrent requests. State bleeds between unrelated requests. Tests become order-dependent. Horizontal scaling is impossible because state lives in one process.

**Recommended fix direction:** Encapsulate the mutable state behind a class with explicit access methods, move it to an external store (Redis, database), or scope it per request via dependency injection.

---

### AP-08 — Asynchronous Pyramid of Doom

**Severity:** HIGH

**Concept:** Asynchronous operations are composed by nesting their continuations inside each other, instead of using the language's first-class composition primitive (promises, futures, async/await, channels).

**Semantic Signals:**
- Three or more levels of nested callbacks / handlers, each describing the next async step.
- Error handling repeated in each nesting level with the same boilerplate.
- A handler whose visual shape is a triangle of indentation drifting to the right.
- Sequential async operations composed by passing each one as the completion of the previous one, when the language offers a flatter alternative.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-08`

**Impact:** Code is hard to read and maintain. Error paths are inconsistent. Adding a step requires deepening the nesting.

**Recommended fix direction:** Convert to the language's flat async composition (`async/await`, promise chaining, futures combinators, coroutines).

---

### AP-09 — Missing Environment Configuration

**Severity:** HIGH

**Concept:** Configuration that should vary between development, staging, and production is hardcoded in source files, forcing a code change for every deployment difference.

**Semantic Signals:**
- The entry point sets port, host, debug flag, database path, or log level via literals rather than reading from environment / config.
- A configuration-loading library is listed as a dependency but is never imported or used.
- The same constant appears as a literal in multiple files, with no central configuration module.
- No `.env.example` (or equivalent template) exists in the repository.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-09`

**Impact:** Configuration cannot differ between environments without code edits. Secrets become visible in source. Deployment becomes brittle.

**Recommended fix direction:** Centralize configuration in a single module that reads from environment variables, with safe defaults for development. Provide a `.env.example` template.

---

## MEDIUM

---

### AP-10 — N+1 Query Pattern

**Severity:** MEDIUM

**Concept:** Code retrieves a collection of records, then issues one additional query per record to load related data, producing N+1 database round-trips where one (with a join or batch load) would suffice.

**Semantic Signals:**
- A loop iterating over results of a query, with another query issued inside the loop body — usually to fetch a related entity by foreign key.
- ORM code that accesses a relationship attribute lazily inside a loop, with no eager-loading directive on the parent query.
- Repeated per-item lookups against a small reference table that could be loaded once into a map.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-10`

**Impact:** Performance degrades linearly with data size. A list of 1,000 records may trigger 1,001 queries. DB connections saturate under modest load.

**Recommended fix direction:** Use eager loading (join-load / batch-load), express the relationship as a single SQL JOIN, or pre-fetch related entities with an `IN (...)` query and join in memory.

---

### AP-11 — Bare / Generic Exception Handling

**Severity:** MEDIUM

**Concept:** Exceptions are caught with no type discrimination, then silently swallowed or replaced with a generic error response, masking the original failure.

**Semantic Signals:**
- A `catch` / `except` block that captures every possible error (no type, or the language's root exception type) without logging it.
- A `catch` block whose body is empty or returns a hardcoded "something went wrong" message.
- Catch blocks that swallow exception types meant to terminate the process (interrupts, system exits, out-of-memory).
- The same broad catch repeated across many handlers with no central error handler.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-11`

**Impact:** Debugging is impossible because the original cause is lost. Critical signals (interrupts, OOM) are silenced. Data inconsistency from half-completed operations goes undetected.

**Recommended fix direction:** Catch specific, expected exception types. Log the cause with a stack trace at the appropriate severity. Centralize "last resort" handling in a single error middleware.

---

### AP-12 — Debug / Verbose Mode Enabled by Default

**Severity:** MEDIUM

**Concept:** The application ships with a debug flag, interactive debugger, or verbose error output enabled unconditionally — exposing internal state and execution paths to anyone who can reach the application.

**Semantic Signals:**
- A debug-mode toggle set to a truthy literal in the entry point with no environment check around it.
- An error-handling middleware that returns full stack traces and source paths in HTTP responses without checking the environment.
- A built-in interactive debugger (or REPL) enabled in production-bound configuration.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-12`

**Impact:** Stack traces leak internal paths, library versions, and code structure to attackers. Some debug consoles expose remote code execution to anyone who can trigger an exception.

**Recommended fix direction:** Gate the debug flag on the environment (`debug = env == "development"`). Keep production responses generic; log details server-side.

---

### AP-13 — Duplicated Logic (DRY Violation)

**Severity:** MEDIUM

**Concept:** The same non-trivial logic appears in two or more places, drifting out of sync as one copy is fixed but others are not.

**Semantic Signals:**
- A multi-line block (5+ lines) of domain logic appears, near-verbatim, in two or more files.
- The same validation, calculation, or formatting is implemented once in a model and again in a handler.
- Identical pagination, filter, or query-building snippets copy-pasted across multiple list endpoints.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-13`

**Impact:** Bug fixes must be applied N times; in practice one or more copies are missed. The codebase diverges in subtle ways that surface as user-visible inconsistencies.

**Recommended fix direction:** Extract the logic into a single function on the appropriate layer (model method for entity-level rules; service function for cross-entity orchestration; utility for generic concerns).

---

### AP-14 — Deprecated API Usage

**Severity:** MEDIUM

**Concept:** The code uses an API that the language, runtime, or framework has marked as deprecated, scheduled for removal, or already replaced by a modern equivalent.

**Semantic Signals:**
- An import or call to a symbol that the language's official upgrade notes flag as deprecated.
- Use of a "compatibility" or "contrib" namespace removed in the major version listed in the manifest.
- Calls returning naive (timezone-less) datetimes when the language has moved to timezone-aware defaults.
- Constructor calls to types whose constructor has been deprecated in favor of a factory.
- Symmetric cipher APIs that take no IV (deprecated forms of an older crypto interface).

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-14`

**Impact:** Code breaks on the next runtime upgrade. Some deprecated APIs have known security issues that motivated their removal (e.g., no-IV cipher constructors).

**Recommended fix direction:** Replace each deprecated symbol with its modern equivalent. Pin the runtime version in the manifest to match.

---

## LOW

---

### AP-15 — Magic Numbers and Magic Strings

**Severity:** LOW

**Concept:** Literal values that carry domain meaning (status codes, thresholds, percentages, role names, state machine values) appear inline in code with no name, definition, or central reference.

**Semantic Signals:**
- Numeric literals used in business comparisons or calculations with no obvious meaning (`if status == 1`, `price * 0.15`).
- String literals representing states (`"pending"`, `"active"`, `"completed"`) repeated across multiple files with no constant or enum.
- HTTP status codes hardcoded as integers across many handlers rather than referenced by name.
- Threshold values (limits, batch sizes, retry counts) buried inline.

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-15`

**Impact:** Intent is opaque without context. Changing the value requires a fragile global search-replace. Inconsistencies between copies are common.

**Recommended fix direction:** Promote to named constants in a dedicated module (or enum where the language supports it). Reference the name everywhere.

---

### AP-16 — Poor Naming Conventions

**Severity:** LOW

**Concept:** Identifiers are too short, too cryptic, or too generic to convey intent — making the code harder to read than necessary.

**Semantic Signals:**
- Single-letter variables outside well-understood contexts (loop indices, exception aliases).
- Abbreviations that are not part of the project's domain glossary (`usr`, `prd`, `ord`, `calc_ov`).
- Function names that describe mechanism instead of intent (`do_thing`, `process`, `handle`, `run`).
- Boolean variables not phrased as a yes/no question (`overdue` instead of `is_overdue`, `ready` instead of `is_ready`).

**Stack-specific signals:** `stack-adapters/<stack>.md § AP-16`

**Impact:** New contributors spend extra effort building a mental model. Refactors are riskier because the code's intent isn't self-explanatory.

**Recommended fix direction:** Use names that reveal purpose. Follow the language's idiomatic casing convention consistently throughout.
