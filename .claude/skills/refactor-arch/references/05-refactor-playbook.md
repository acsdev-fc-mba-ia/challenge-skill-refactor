# Refactoring Playbook

Each entry maps one anti-pattern from `02-antipattern-catalog.md` to a concrete sequence of steps that fix it.

The steps below describe **what to do conceptually**. Concrete before/after code in the active language lives in `stack-adapters/<stack>.md § <PB-id>` and must be consulted alongside this file when executing Phase 3.

If no adapter exists for the detected stack, the steps here are still sufficient — they describe transformations at the level of code structure and intent, not syntax.

Apply transformations in the order given in **§ Application Order** at the end of this file.

---

## PB-01 — Hardcoded Secrets → Environment Variables

**Fixes:** AP-01 (Hardcoded Secrets), AP-09 (Missing Environment Configuration)

**Steps:**

1. Inventory every literal value that matches the AP-01 signals (secrets, keys, URLs, hosts, debug flags).
2. Create `config/` if absent. Add a single module that reads each value from the environment and exposes it as a named constant. Provide development-safe defaults only for non-sensitive values; secrets default to `None` / unset.
3. Replace every original literal in source files with an import from `config/`.
4. Create `.env.example` listing every variable, with placeholder values (no real secrets).
5. Add the language's `.env`-loading library to dependencies if not already present, and invoke it once at the start of `config/`.
6. Verify by searching the codebase for the original literal values: zero occurrences should remain outside `.env.example` and tests.

**Adapter:** `stack-adapters/<stack>.md § PB-01`

---

## PB-02 — Unsafe SQL Strings → Parameterized Queries

**Fixes:** AP-02 (SQL Injection via String Interpolation)

**Steps:**

1. Locate every call site where the SQL argument is built by concatenation, formatting, or template expansion. Each one is a finding.
2. For each call site, rewrite the SQL string to use the driver's parameter placeholders (`?`, `$N`, `:name` — pick the placeholder style the driver supports).
3. Move the previously interpolated values into the driver's bind-parameter argument list.
4. Where the same query is built dynamically from optional filters, use a query-builder or ORM expression API instead of string concatenation.
5. **Preferred upgrade:** if no ORM is in use, introduce one for new code, and migrate the high-risk queries first (those that touch authentication, payment, or admin domains).
6. Verify by searching for string-concatenation operators adjacent to SQL keywords (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) — zero hits should remain.

**Adapter:** `stack-adapters/<stack>.md § PB-02`

---

## PB-03 — God File → MVC Decomposition

**Fixes:** AP-03 (God Class / God File)

**Steps:**

1. List every responsibility currently held by the god file: routes, persistence, business logic, integrations, helpers.
2. Identify the domain entities involved (users, products, tasks, etc.). One entity = one set of files.
3. For each entity, create the four-layer set: `models/<entity>`, `services/<entity>_service`, `controllers/<entity>_controller`, `routes/<entity>_routes`.
4. Move code from the god file into the matching layer, **one entity at a time**. Do not start a second entity until the first is fully migrated and the app still boots.
5. Update the composition root to register the new routes and remove the inlined handlers.
6. Delete the god file once empty (or keep the file only if it now holds genuinely cross-cutting glue — composition only).

**Rule:** never let two distinct domains share a file in any layer.

**Adapter:** `stack-adapters/<stack>.md § PB-03`

---

## PB-04 — Dangerous Admin Endpoint → Remove or Constrain

**Fixes:** AP-04 (Arbitrary Code / SQL Execution Endpoint)

**Steps:**

1. **Default action:** delete the endpoint. There is rarely a legitimate reason to keep it.
2. If after audit the endpoint is genuinely required, replace the free-form payload with a strict allow-list of named operations. The handler accepts a name + parameters; the names map to fixed, hand-written queries or operations.
3. Add authentication and authorization to the endpoint — it must require a privileged role.
4. Log every invocation with caller identity, operation name, and parameters.
5. Update the endpoint inventory: if deleted, remove from `api.http`; if constrained, document the new contract.

**Adapter:** `stack-adapters/<stack>.md § PB-04`

---

## PB-05 — Weak Crypto → Standard Primitive

**Fixes:** AP-05 (Weak / Custom Cryptography)

**Steps:**

1. Identify every hashing or encryption call. Classify each as: password hashing, data-at-rest encryption, transport, or signing.
2. Pick the appropriate standard primitive for each class:
   - **Password hashing:** `bcrypt`, `argon2`, or `scrypt`.
   - **Symmetric encryption:** authenticated mode (e.g., AES-GCM) with per-message IV.
   - **Signing:** HMAC-SHA-256 with a properly stored key.
3. Replace the custom code with a call to a vetted library that exposes the chosen primitive.
4. **Migrate stored data:** for passwords, re-hash on next successful login (compare old hash on login; on success, write the new hash). Do not bulk-migrate without a way to verify.
5. Remove the custom crypto code entirely once the migration path is in place.

**Adapter:** `stack-adapters/<stack>.md § PB-05`

---

## PB-06 — Business Logic in Routes → Service Extraction

**Fixes:** AP-06 (Business Logic in Handlers)

**Steps:**

1. Identify the domain operation the handler is performing (e.g., "list tasks with overdue status", "process checkout").
2. Create or extend a service module for that entity. Add a method that takes plain inputs (not request objects) and returns plain outputs (not response objects).
3. Move all calculations, lookups, status transitions, and side-effects from the handler into the new service method.
4. Reduce the handler to three actions: parse request inputs, call the service, serialize the result.
5. Map service exceptions to HTTP status codes in the controller — never let the service know about HTTP.

**Adapter:** `stack-adapters/<stack>.md § PB-06`

---

## PB-07 — Async Pyramid → Flat Composition

**Fixes:** AP-08 (Asynchronous Pyramid of Doom)

**Steps:**

1. Identify the chain of dependent async operations buried in the nesting.
2. Rewrite using the language's flat composition primitive (`async/await`, future combinators, coroutines, channels — whatever is idiomatic for the stack).
3. Replace per-callback error handling with a single `try/catch` (or equivalent) around the flattened sequence.
4. Where the driver only exposes a callback API, wrap it once in a promise / future helper at the driver boundary; do not propagate callbacks upward.
5. Consider switching to a synchronous-style driver if the runtime supports it and the data volume permits.

**Adapter:** `stack-adapters/<stack>.md § PB-07`

---

## PB-08 — Global State → Encapsulation

**Fixes:** AP-07 (Global Mutable State)

**Steps:**

1. Identify each module-level mutable variable that handlers write to.
2. For each one, create a class (or equivalent encapsulation) that holds the state as private and exposes explicit access methods (`add`, `get`, `reset`).
3. Instantiate the class once at startup (composition root or service module). Inject the instance into the services that need it.
4. Add concurrency control if the underlying state can race (locks, atomics, or thread-safe data structures).
5. **Preferred path:** if the state is genuinely shared, move it to an external store (Redis, database). In-process global state cannot survive horizontal scaling.

**Adapter:** `stack-adapters/<stack>.md § PB-08`

---

## PB-09 — N+1 Queries → Eager Loading

**Fixes:** AP-10 (N+1 Query Pattern)

**Steps:**

1. Identify queries inside loops that load related entities one row at a time.
2. Rewrite the parent query to fetch the related data in a single round-trip:
   - With an ORM: use eager-loading directives (`joinedload`, `selectinload`, `include`, `with`).
   - With raw SQL: write a `JOIN` that returns the parent and related columns together.
   - With document stores or external services: batch-load related IDs with a single bulk request.
3. Move the loading logic up to the service layer. The handler should never trigger a relationship lookup directly.
4. Verify by counting database queries on the affected endpoint (use the driver's logging, or an APM/profiler) — it must be constant, not proportional to row count.

**Adapter:** `stack-adapters/<stack>.md § PB-09`

---

## PB-10 — Bare Catch → Specific Exception Handling

**Fixes:** AP-11 (Bare Exception Handling)

**Steps:**

1. For each broad catch block, identify the exceptions the inner code actually raises.
2. Replace the broad catch with one or more catches for those specific types. Map each to an appropriate response or recovery action.
3. **Always log** the original exception with stack trace before transforming it into a response.
4. Let interrupts, system-exits, and other framework-level signals propagate. Never catch the language's root exception type unless you immediately log and re-raise.
5. Move "last resort" handling into a centralized error middleware (`middleware/error_handler`). Handler code should not duplicate generic 500 responses.

**Adapter:** `stack-adapters/<stack>.md § PB-10`

---

## PB-11 — Deprecated APIs → Modern Equivalents

**Fixes:** AP-14 (Deprecated API Usage)

**Steps:**

1. For each deprecated symbol found in Phase 2, look up its modern replacement in the language's official upgrade notes (the stack adapter lists the common ones).
2. Replace all call sites. Where the new API takes additional arguments (e.g., IV for ciphers, timezone for datetimes), provide them explicitly.
3. Update the dependency manifest if the modern API requires a newer library version.
4. Run the project's import resolver / linter to confirm no further deprecation warnings remain.

**Adapter:** `stack-adapters/<stack>.md § PB-11`

---

## PB-12 — Duplicated Logic → Single Source of Truth

**Fixes:** AP-13 (Duplicated Logic)

**Steps:**

1. Identify each duplicated block. Pick the layer where the logic belongs (model method for entity-level rules, service for cross-entity orchestration, utility for generic concerns).
2. Move one copy to that location. Make it the canonical implementation.
3. Replace every other copy with a call to the canonical version.
4. Delete the now-unused copies.
5. Verify by re-searching for the original pattern: only the canonical implementation should remain.

**Adapter:** `stack-adapters/<stack>.md § PB-12`

---

## PB-13 — Magic Values → Named Constants

**Fixes:** AP-15 (Magic Numbers and Magic Strings)

**Steps:**

1. Inventory literals carrying domain meaning (status values, thresholds, percentages, role names).
2. Create a constants module (or use the language's enum feature for closed sets like status values).
3. Define each value once with a descriptive name.
4. Replace every inline occurrence with a reference to the named constant.
5. Verify by searching for the original literal: only the definition should remain.

**Adapter:** `stack-adapters/<stack>.md § PB-13`

---

## PB-14 — Poor Names → Intent-Revealing Names

**Fixes:** AP-16 (Poor Naming Conventions)

**Steps:**

1. List identifiers flagged in Phase 2 (single letters outside loops, cryptic abbreviations, mechanism-named functions, ambiguous booleans).
2. Choose names that describe purpose, not implementation.
3. Apply the language's idiomatic casing convention consistently.
4. Use the IDE's safe-rename refactor — never do this by hand if a rename tool is available, to avoid catching unrelated tokens.

**Adapter:** `stack-adapters/<stack>.md § PB-14`

---

## Application Order

Apply transformations in this sequence to minimize the risk of breaking the application mid-refactor:

1. **PB-01** — Extract configuration and secrets first. Nothing else can safely proceed without a clean config layer.
2. **PB-03** — Create the target directory structure with empty skeleton files. The app should still boot at this point.
3. **PB-04** — Remove dangerous endpoints immediately. They are zero-benefit risks.
4. **PB-02** — Fix SQL interpolation in every model / data file.
5. **PB-05** — Replace weak crypto.
6. **PB-06** — Move business logic from handlers to services, one domain at a time.
7. **PB-09** — Fix N+1 queries (services are now the right home for the join logic).
8. **PB-07** — Flatten async (Node.js / any callback-heavy stack), after services are extracted.
9. **PB-08** — Encapsulate global state, after services are extracted.
10. **PB-10** — Tighten exception handling across all layers.
11. **PB-11, PB-12, PB-13, PB-14** — Apply remaining MEDIUM/LOW fixes.
12. **Validate** by running every request in the endpoint inventory and confirming the same behavior as before refactoring.

After every numbered step, the application must still boot. If a step breaks the boot, revert that step before continuing.
