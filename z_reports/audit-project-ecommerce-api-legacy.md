================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code
Date:    2026-05-17

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 3 | LOW: 2
Total findings: 12

## Findings

### [CRITICAL] Hardcoded Secrets / Credentials
File: src/utils.js:1-7
Description: The `config` object exports four production secrets as string literals: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `dbUser: "admin_master"`, and `smtpUser: "no-reply@fullcycle.com.br"`. All four are committed to version control in plain text.
Impact: Anyone with read access to the repository can steal the payment gateway key and database credentials, enabling fraudulent charges and direct database access in production.
Recommendation: Move all four to a `.env` file loaded via `dotenv`; expose through a config module reading `process.env.*`; commit a `.env.example` with placeholder values.

### [CRITICAL] God Class / God File
File: src/AppManager.js:1-141
Description: The `AppManager` class concentrates five distinct responsibilities in 141 lines: database schema creation and seeding (`initDb`, lines 10–23), HTTP route registration (`setupRoutes`, lines 25–138), checkout business logic including payment processing and user creation (lines 28–78), financial report aggregation (lines 80–129), and delegated cryptography via `badCrypto` (line 68). No separation of concerns exists.
Impact: Any change to one concern (e.g., adding a route or fixing a payment rule) risks breaking the others; the class cannot be unit-tested in isolation without starting a full HTTP server.
Recommendation: Decompose into `services/checkoutService.js`, `services/reportService.js`, `controllers/checkoutController.js`, `controllers/reportController.js`, and `routes/` files per domain; keep the composition root minimal.

### [CRITICAL] Weak / Custom Cryptography
File: src/utils.js:17-23
Description: The `badCrypto()` function stores passwords by applying `Buffer.from(pwd).toString('base64')` in a 10,000-iteration loop and truncating the result to 10 characters. Base64 is an encoding, not a hash — the output is deterministic, has no salt, and is trivially reversible.
Impact: The entire password database can be cracked instantly; all stored passwords are effectively plaintext.
Recommendation: Replace `badCrypto` with `bcrypt.hash(plain, 12)` from the `bcryptjs` package; use `bcrypt.compare` for verification.

### [HIGH] Business Logic Embedded in Route / Controller Handlers
File: src/AppManager.js:28-78
Description: The `POST /api/checkout` handler performs all of the following inline: course availability lookup, user existence check, new user creation, payment approval decision (`cc.startsWith("4")`), enrollment insert, payment record insert, and audit log insert — 50 lines of domain logic mixed with HTTP request parsing and response sending.
Impact: The checkout rule cannot be tested without a running HTTP server and database; adding a new payment method or discount requires editing a deeply nested callback chain.
Recommendation: Extract checkout orchestration into `services/checkoutService.js`; the handler should only parse the request, call the service, and return the response.

### [HIGH] Global Mutable State
File: src/utils.js:9-10
Description: `let globalCache = {}` and `let totalRevenue = 0` are declared as module-level mutable variables. `globalCache` is written from every checkout request via `logAndCache()` (AppManager.js line 59) with no locking or encapsulation.
Impact: Concurrent requests corrupt cache entries and revenue totals; state bleeds between test runs; horizontal scaling is impossible because state lives only in a single process.
Recommendation: Encapsulate `globalCache` in a `CacheService` class with explicit `get`/`set` methods; persist `totalRevenue` in the database rather than in module scope.

### [HIGH] Asynchronous Pyramid of Doom
File: src/AppManager.js:37-77
Description: The checkout handler nests five callback levels: `db.get(course)` → `db.get(user)` → `db.run(enrollment)` → `db.run(payment)` → `db.run(audit_log)`, each with its own inline error guard, producing a right-drifting triangle of indentation reaching 6+ levels deep.
Impact: Adding a new step (e.g., sending a confirmation email) requires deepening the nesting; error paths at each level have inconsistent handling, and the full flow is impossible to follow at a glance.
Recommendation: Switch to `better-sqlite3` (synchronous) or promisify `sqlite3` calls and refactor to `async/await` in a service function, flattening all five steps to sequential awaits.

### [HIGH] Missing Environment Configuration
File: src/utils.js:1-7
Description: All deployment configuration — database credentials, payment gateway key, SMTP user, and server port — are hardcoded literals in `utils.js`. There is no `dotenv` dependency, no `process.env` call, and no `.env.example` file in the repository.
Impact: Configuration cannot differ between development and production without editing source; secrets are visible in version control; deployment automation cannot inject runtime config.
Recommendation: Add `dotenv` to dependencies, call `require('dotenv').config()` at startup, read all values via `process.env.*`, and commit a `.env.example` with placeholder values.

### [MEDIUM] N+1 Query Pattern
File: src/AppManager.js:89-128
Description: The `GET /api/admin/financial-report` handler issues `db.all("SELECT * FROM courses")`, then for each course issues `db.all("SELECT * FROM enrollments WHERE course_id = ?")`, and for each enrollment issues two separate queries: `db.get(user)` and `db.get(payment)` — producing up to 1 + N + 2×M round-trips for N courses and M total enrollments.
Impact: With 10 courses and 100 enrollments, the report issues 211 queries; under moderate load this saturates the database connection and causes severe latency.
Recommendation: Replace the nested loops with a single JOIN query across `courses`, `enrollments`, `users`, and `payments`, then aggregate in memory.

### [MEDIUM] Bare / Generic Exception Handling
File: src/AppManager.js:104-137
Description: Three database callbacks suppress errors silently: the `db.get(user)` callback at line 104, the `db.get(payment)` callback at line 106, and the `db.run("DELETE")` callback at line 133 — none check the `err` argument, so database failures in financial reports and user deletions are swallowed without any response or log.
Impact: A database failure during financial-report generation returns a partial or empty result with HTTP 200; a failed DELETE returns the success message regardless of whether the row was actually removed; root causes are invisible.
Recommendation: Check `err` in every callback and either call `next(err)` or return an error response; centralize handling in an Express error-handler middleware.

### [MEDIUM] Debug / Verbose Mode Enabled by Default
File: src/AppManager.js:45
Description: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` logs the full credit card number from the request and the live payment gateway key to standard output unconditionally on every checkout, with no environment check.
Impact: In production, card numbers and the payment key are written to any log aggregation system or console accessible to infrastructure staff, violating PCI-DSS cardholder data requirements.
Recommendation: Remove this log entirely or, if diagnostics are needed, log only a masked card suffix (`****${cc.slice(-4)}`) gated on `NODE_ENV === 'development'`; never log the payment gateway key.

### [LOW] Magic Numbers and Magic Strings
File: src/AppManager.js:46-108
Description: The payment approval decision uses the magic string `"4"` (`cc.startsWith("4")`) to identify Visa cards inline at line 46; payment statuses `"PAID"` and `"DENIED"` appear as string literals at lines 46, 54, and 108 without a shared constant.
Impact: Changing the approval logic or adding a new card brand requires a fragile search-replace; a typo in one status string creates an invisible logic error.
Recommendation: Define `const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' })` and `const CardBrand = Object.freeze({ VISA_PREFIX: '4' })` in a `constants.js` module.

### [LOW] Poor Naming Conventions
File: src/AppManager.js:29-33
Description: The checkout handler destructures five request fields into single-letter or abbreviated variables: `u` (username), `e` (email), `p` (password), `cid` (courseId), `cc` (creditCard). Inside the `forEach` at line 89, courses are bound to `c`, obscuring intent throughout the financial report logic.
Impact: Every reader must mentally decode the abbreviations before understanding the code; the variables `e` (email) and `enrId` (enrollmentId) share the same first letter, increasing cognitive load.
Recommendation: Rename to `username`, `email`, `password`, `courseId`, `creditCard`, and `course` respectively, following the camelCase convention used elsewhere in the file.

================================
