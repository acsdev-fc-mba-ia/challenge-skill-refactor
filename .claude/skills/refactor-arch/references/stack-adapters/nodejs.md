# Stack Adapter — Node.js

Concrete signals, idioms, and code examples for Node.js / JavaScript / TypeScript projects. Loaded conditionally by `SKILL.md` after Phase 1 detects Node.js.

This adapter implements the language-specific layer described abstractly in `02-antipattern-catalog.md`, `04-architecture-guidelines.md`, and `05-refactor-playbook.md`.

---

## Framework Map

| Package in dependencies | Framework |
|---|---|
| `express` | Express |
| `fastify` | Fastify |
| `koa` | Koa |
| `@hapi/hapi` | Hapi |
| `@nestjs/core` | NestJS |
| `restify` | Restify |
| `next` | Next.js (API routes) |

Read the version from `package.json` (e.g., `"express": "^4.18.2"` → Express 4.18.2).

---

## ORM / Database Drivers

| Import | Layer |
|---|---|
| `require('sequelize')` / `from 'sequelize'` | Sequelize ORM |
| `require('@prisma/client')` | Prisma |
| `require('typeorm')` | TypeORM |
| `require('knex')` | Knex query builder |
| `require('mongoose')` | Mongoose (MongoDB) |
| `require('sqlite3')` | sqlite3 driver (callback-based) |
| `require('better-sqlite3')` | better-sqlite3 (synchronous) |
| `require('pg')` | PostgreSQL driver |
| `require('mysql2')` | MySQL driver |

Raw-SQL signals: `db.run(`, `db.all(`, `db.get(`, `db.exec(`, `client.query(`, presence of `CREATE TABLE` literals in source.

---

## Layout (idiomatic)

```
<project-root>/
├── .env.example
├── package.json
├── src/
│   ├── index.js                # composition root
│   ├── database.js
│   ├── config/
│   │   └── index.js
│   ├── models/
│   │   ├── User.js
│   │   └── Course.js
│   ├── services/
│   │   ├── userService.js
│   │   └── checkoutService.js
│   ├── controllers/
│   │   ├── userController.js
│   │   └── checkoutController.js
│   ├── routes/
│   │   ├── userRoutes.js       # express.Router() per domain
│   │   └── checkoutRoutes.js
│   └── middleware/
│       └── errorHandler.js
```

**File naming:** `camelCase.js` for modules; `PascalCase.js` for class/model files. **Class naming:** `PascalCase`. **Function naming:** `camelCase`. **Constants:** `UPPER_SNAKE_CASE`.

---

## AP-01 — Hardcoded Secrets (Node.js signals)

Patterns to grep for:
- `const SECRET = "<literal>"`, `const API_KEY = "..."`
- `const DB_CREDENTIALS = { user: 'admin', password: 'admin123' }`
- `const PAYMENT_KEY = "sk_live_..."`
- Object literals exporting credentials: `module.exports = { user: 'admin', password: '...' }`
- JWT secrets, signing keys, OAuth client secrets as string literals.

What is NOT a finding: values read from `process.env.X` or a config module that wraps `dotenv.config()`.

---

## AP-02 — SQL Injection (Node.js signals)

Patterns to grep for:
- `` db.get(`SELECT * FROM users WHERE id = ${id}`) `` — template literal
- `db.run("SELECT * FROM users WHERE email = '" + email + "'")` — concatenation
- `client.query("SELECT * FROM users WHERE id = " + id)` — `pg` concat
- Any DB driver call (`run`, `all`, `get`, `exec`, `query`) whose first argument is the result of a string operation.

Safe forms: `db.get("SELECT * FROM users WHERE id = ?", [id])` (sqlite3), `client.query("SELECT * FROM users WHERE id = $1", [id])` (pg), Sequelize/Prisma/TypeORM expression APIs.

---

## AP-03 — God File (Node.js signals)

- Classes named `AppManager`, `Application`, `Server` > 100 LOC mixing route registration, DB init, business logic, crypto, reporting.
- A single `src/index.js` or `src/app.js` with all route handlers inlined as `app.post(...)` declarations.
- A `controllers/` file mixing handlers for multiple domains.

---

## AP-04 — Dangerous Admin Endpoint (Node.js signals)

- `app.post('/admin/query', (req, res) => db.run(req.body.query, ...))`
- Handlers reading `req.body.sql`, `req.body.cmd`, `req.body.code` and passing to `eval`, `Function(...)`, `vm.runInNewContext`, `child_process.exec`, or a DB driver.

---

## AP-05 — Weak Crypto (Node.js signals)

- `Buffer.from(password).toString('base64')` presented as hashing (even in a loop).
- `crypto.createHash('md5')` / `crypto.createHash('sha1')` for passwords.
- `crypto.createCipher(...)` — deprecated, no IV. Always a finding.
- Custom XOR / character-shift "encryption".
- Plain `==` comparison of password hashes (vulnerable to timing attacks; use `crypto.timingSafeEqual`).

Recommended replacement: `bcryptjs` or `argon2` package; `crypto.createCipheriv` with AES-GCM.

---

## AP-06 — Business Logic in Handlers (Node.js signals)

- Route handlers (`app.post`, `router.get`) with > 5 lines of logic between request parsing and `res.json(...)`.
- Date math, price math, status transitions, conditional notification sending inline in the handler.

---

## AP-07 — Global Mutable State (Node.js signals)

- Module-level `let globalCache = {}` mutated inside request handlers.
- Module-level `let totalRevenue = 0` with `totalRevenue += amount` inside a handler.
- Class static properties used as counters: `class Foo { static count = 0; }` followed by `Foo.count++` in a handler.

---

## AP-08 — Callback Hell (Node.js signals)

- Three or more levels of nested callbacks of the form `(err, result) => { ... }`.
- A handler whose body forms a visible triangle of right-drifting indentation.
- Sequential `db.get(... , (err, row) => db.run(... , (err, ...) => ...))` chains where each level repeats the same error guard.

---

## AP-09 — Missing Environment Configuration (Node.js signals)

- `app.listen(3000)` with a literal port and no `process.env.PORT` fallback.
- `const DB_PATH = ':memory:'` hardcoded.
- `dotenv` listed in `dependencies` but never `require`-d.
- No `.env.example` at the project root.

---

## AP-10 — N+1 Queries (Node.js signals)

- `rows.forEach(row => db.get('SELECT * FROM users WHERE id = ?', [row.userId], ...))` — query in loop.
- Sequelize: `tasks.map(t => User.findByPk(t.userId))` without `include: [User]`.
- Prisma: `tasks.map(t => prisma.user.findUnique({ where: { id: t.userId } }))` without `include`.

---

## AP-11 — Bare Exception Handling (Node.js signals)

- `try { ... } catch (e) {}` — empty catch.
- `catch (e) { return null }` — silent swallow.
- `catch (e) { res.status(500).json({ error: 'something went wrong' }) }` without `console.error(e)` / `logger.error(e)`.
- Unhandled promise rejections (missing `.catch` on a chain, or no `await` inside `try`).

---

## AP-12 — Debug Mode (Node.js signals)

- Error-handling middleware that returns `err.stack` in the JSON response without checking `NODE_ENV`.
- `console.log` of secrets or full request bodies in production paths.
- Source maps shipped to production exposing original file paths.

---

## AP-13 — Duplicated Logic (Node.js signals)

- The same multi-line block (e.g., user-permission check, pagination math) repeated across `routes/*.js` files.
- Identical formatting / serialization logic in multiple controllers.

---

## AP-14 — Deprecated APIs (Node.js signals)

| Deprecated | Replacement | Removed in |
|---|---|---|
| `new Buffer(...)` | `Buffer.from(...)` / `Buffer.alloc(...)` | Deprecated since Node 6 |
| `crypto.createCipher` / `createDecipher` | `createCipheriv` / `createDecipheriv` | Removed in Node 22 |
| `url.parse(...)` | `new URL(...)` | Deprecated since Node 11 |
| `util.isArray`, `util.isString`, etc. | `Array.isArray()`, `typeof === 'string'` | Deprecated since Node 4 |
| `require('node:punycode')` | external `punycode/` package | Deprecated in Node 21 |
| `fs.exists` | `fs.access` / `fs.existsSync` | Deprecated since Node 1 |
| Express 4 `body-parser` separate | built-in `express.json()` / `express.urlencoded()` | Express 4.16+ |

---

## AP-15 — Magic Values (Node.js signals)

- `if (order.status === 1) ...` — numeric status without enum/constant.
- `if (cc.startsWith("4")) ...` — magic credit-card prefix (Visa) without a constant.
- HTTP status codes as numeric literals: `res.status(404).json(...)` repeated 10+ times instead of using `http.STATUS_CODES` or named constants.

---

## AP-16 — Poor Names (Node.js signals)

- Single-letter variables outside short callbacks: `u`, `e`, `p`, `cid`, `cc` for user, email, password, course-id, credit-card.
- Function names like `doStuff`, `process`, `handle`.
- Boolean variables not phrased as predicates: `overdue` instead of `isOverdue`.

---

## PB-01 — Hardcoded Secrets → Environment Variables (Node.js)

**Before:**
```js
const DB_CREDENTIALS = { user: 'admin', password: 'admin123' };
const PAYMENT_KEY = 'sk_live_abc123xyz';
const SMTP_USER = 'noreply@company.com';
```

**After:**
```js
require('dotenv').config();

if (!process.env.PAYMENT_KEY) {
    throw new Error('PAYMENT_KEY must be set');
}

module.exports = {
    dbPath: process.env.DB_PATH || ':memory:',
    paymentKey: process.env.PAYMENT_KEY,
    smtpUser: process.env.SMTP_USER,
    smtpPassword: process.env.SMTP_PASSWORD,
    port: parseInt(process.env.PORT || '3000', 10),
};
```
```
# .env.example
DB_PATH=:memory:
PAYMENT_KEY=replace-me
SMTP_USER=noreply@example.com
SMTP_PASSWORD=replace-me
PORT=3000
```

---

## PB-02 — SQL Injection → Parameterized Queries (Node.js)

**Before:**
```js
db.get(`SELECT * FROM users WHERE email = '${email}'`, (err, row) => { ... });
```

**After (minimum — placeholders):**
```js
db.get('SELECT * FROM users WHERE email = ?', [email], (err, row) => { ... });
```

**After (preferred — better-sqlite3 + named queries):**
```js
const stmt = db.prepare('SELECT * FROM users WHERE email = ?');
const user = stmt.get(email);
```

---

## PB-03 — God File → MVC (Node.js)

Decompose a 141-LOC `AppManager.js` (DB + routes + business + crypto) into:

```
src/
  models/
    User.js          # class or ORM model
    Course.js
  services/
    checkoutService.js   # enrollment + payment logic
    reportService.js     # financial aggregation
  controllers/
    checkoutController.js
    reportController.js
  routes/
    checkoutRoutes.js    # router.post('/api/checkout', controller.process)
    reportRoutes.js
  index.js               # composition root only
```

---

## PB-04 — Dangerous Admin Endpoint → Removal (Node.js)

**Before:**
```js
app.post('/admin/query', (req, res) => {
    db.all(req.body.query, (err, rows) => res.json(rows));
});
```

**After:** delete the endpoint. If a constrained subset is needed:
```js
const ALLOWED_REPORTS = {
    user_count: 'SELECT COUNT(*) AS n FROM users',
    order_count: 'SELECT COUNT(*) AS n FROM orders',
};

router.get('/reports/:name', requireAdmin, (req, res) => {
    const sql = ALLOWED_REPORTS[req.params.name];
    if (!sql) return res.status(404).json({ error: 'unknown report' });
    const row = db.prepare(sql).get();
    res.json(row);
});
```

---

## PB-05 — Weak Crypto → bcrypt (Node.js)

**Before:**
```js
function hashPassword(password) {
    let hashed = password;
    for (let i = 0; i < 10000; i++) {
        hashed = Buffer.from(hashed).toString('base64');
    }
    return hashed;
}
```

**After:**
```js
const bcrypt = require('bcryptjs');

async function hashPassword(plain) {
    return bcrypt.hash(plain, 12);
}

async function verifyPassword(plain, hashed) {
    return bcrypt.compare(plain, hashed);
}
```

---

## PB-06 — Business Logic in Routes → Services (Node.js)

**Before:**
```js
app.post('/api/checkout', (req, res) => {
    const { userId, courseId, cc } = req.body;
    db.get('SELECT * FROM users WHERE id = ?', [userId], (err, user) => {
    });
});
```

**After:**
```js
class CheckoutService {
    constructor(db, paymentGateway) { this.db = db; this.gateway = paymentGateway; }
    processCheckout({ userId, courseId, cc }) {
        const user = this.db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
        if (!user) throw new Error('user not found');
        const course = this.db.prepare('SELECT * FROM courses WHERE id = ?').get(courseId);
        if (!course) throw new Error('course not found');
        const payment = this.gateway.charge(cc, course.price);
        this.db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(userId, courseId);
        return { paymentId: payment.id, course: course.title };
    }
}

exports.process = (req, res) => {
    try {
        const result = checkoutService.processCheckout(req.body);
        res.status(201).json(result);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
};

router.post('/checkout', checkoutController.process);
```

---

## PB-07 — Callback Hell → async/await (Node.js)

**Before:**
```js
db.get('SELECT * FROM users WHERE id = ?', [uid], (err, user) => {
    if (err) return res.status(500).json({ error: err.message });
    db.get('SELECT * FROM courses WHERE id = ?', [cid], (err, course) => {
        if (err) return res.status(500).json({ error: err.message });
        db.run('INSERT INTO enrollments VALUES (?, ?)', [uid, cid], (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ ok: true });
        });
    });
});
```

**After (synchronous driver — preferred):**
```js
const Database = require('better-sqlite3');
const db = new Database(config.dbPath);

function enroll(userId, courseId) {
    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
    if (!user) throw new Error('user not found');
    const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(courseId);
    if (!course) throw new Error('course not found');
    db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(userId, courseId);
}
```

**After (async/await with promisified driver):**
```js
const { promisify } = require('util');
const get = promisify(db.get.bind(db));
const run = promisify(db.run.bind(db));

async function enroll(userId, courseId) {
    const user = await get('SELECT * FROM users WHERE id = ?', [userId]);
    if (!user) throw new Error('user not found');
    const course = await get('SELECT * FROM courses WHERE id = ?', [courseId]);
    if (!course) throw new Error('course not found');
    await run('INSERT INTO enrollments VALUES (?, ?)', [userId, courseId]);
}
```

---

## PB-08 — Global State → Encapsulation (Node.js)

**Before:**
```js
let globalCache = {};
let totalRevenue = 0;
```

**After:**
```js
class RevenueService {
    #total = 0;
    add(amount) { this.#total += amount; }
    get total() { return this.#total; }
}
module.exports = new RevenueService();

class CacheService {
    #store = new Map();
    get(key) { return this.#store.get(key); }
    set(key, value) { this.#store.set(key, value); }
    has(key) { return this.#store.has(key); }
}
module.exports = new CacheService();
```

---

## PB-09 — N+1 → JOIN / Eager Loading (Node.js)

**Before:**
```js
const tasks = db.prepare('SELECT * FROM tasks').all();
tasks.forEach(t => {
    t.user = db.prepare('SELECT * FROM users WHERE id = ?').get(t.user_id);
});
```

**After (single JOIN):**
```js
const tasks = db.prepare(`
    SELECT t.*, u.name AS user_name, c.name AS category_name
    FROM tasks t
    LEFT JOIN users u      ON t.user_id = u.id
    LEFT JOIN categories c ON t.category_id = c.id
`).all();
```

**After (Sequelize):**
```js
const tasks = await Task.findAll({ include: [User, Category] });
```

---

## PB-10 — Bare catch → Specific Handling (Node.js)

**Before:**
```js
try {
    const task = await createTask(data);
    res.status(201).json(task);
} catch (e) {
    res.status(500).json({ error: 'something went wrong' });
}
```

**After:**
```js
const logger = require('../logger');

try {
    const task = await createTask(data);
    res.status(201).json(task);
} catch (err) {
    if (err instanceof ValidationError) {
        return res.status(400).json({ error: err.message });
    }
    logger.error({ err }, 'failed to create task');
    res.status(500).json({ error: 'internal error' });
}
```

Centralize the fallback in `middleware/errorHandler.js`:
```js
module.exports = (err, req, res, next) => {
    logger.error({ err, path: req.path }, 'unhandled');
    res.status(err.status || 500).json({ error: err.message || 'internal error' });
};
```

---

## PB-11 — Deprecated APIs (Node.js)

**`new Buffer(...)` → `Buffer.from()` / `Buffer.alloc()`:**
```js
const buf = new Buffer(data);
const zeroed = new Buffer(size);
const buf = Buffer.from(data);
const zeroed = Buffer.alloc(size);
```

**`crypto.createCipher` → `createCipheriv`:**
```js
const cipher = crypto.createCipher('aes-256-cbc', key);
const iv = crypto.randomBytes(16);
const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
```

**`url.parse(...)` → `new URL(...)`:**
```js
const parsed = url.parse(req.url, true);
const parsed = new URL(req.url, `http://${req.headers.host}`);
```

**`util.isArray(x)` → `Array.isArray(x)`** (native check).

---

## PB-12 — Duplicated Logic → Shared Function (Node.js)

**Before:** the same `isOverdue` logic in `routes/taskRoutes.js` and in a model file.

**After:** keep one canonical implementation as a model method.
```js
class Task {
    isOverdue() {
        if (!this.dueDate || this.status === 'completed') return false;
        return new Date() > new Date(this.dueDate);
    }
}
```
Everywhere else: `task.isOverdue()`.

---

## PB-13 — Magic Values → Constants (Node.js)

**Before:**
```js
if (order.status === 1) ...
if (cc.startsWith('4')) ...
res.status(404).json(...);
```

**After:**
```js
const OrderStatus = Object.freeze({
    PENDING: 1, PAID: 2, SHIPPED: 3, CANCELLED: 4,
});
const CardBrand = Object.freeze({
    VISA_PREFIX: '4', MASTERCARD_PREFIX: '5',
});
module.exports = { OrderStatus, CardBrand };

const { OrderStatus, CardBrand } = require('./constants');
const { StatusCodes } = require('http-status-codes');

if (order.status === OrderStatus.PENDING) ...
if (cc.startsWith(CardBrand.VISA_PREFIX)) ...
res.status(StatusCodes.NOT_FOUND).json(...);
```

---

## PB-14 — Poor Names → Intent-Revealing (Node.js)

**Before:** `function proc(d) { ... }`, `let u = ...`, `let overdue = true`

**After:** `function processPayment(data) { ... }`, `let user = ...`, `let isOverdue = true`. Follow camelCase for variables and functions, PascalCase for classes, UPPER_SNAKE_CASE for module-level constants.

---

## Boot & Validation

**Run command (Express):**
```bash
npm install
npm start
```

**Health probe:**
```bash
until curl -sf http://127.0.0.1:3000/ > /dev/null; do sleep 1; done
```

**Common ports:** Express 3000, Fastify 3000, NestJS 3000, Next.js 3000.

**Process management for validation runs:** start in background, capture PID:
```bash
npm start > /tmp/app.log 2>&1 &
APP_PID=$!
# ... run curls ...
kill $APP_PID
```
