---
name: refactor-arch
description: Audits any backend codebase against a catalog of anti-patterns and refactors it into MVC. **USE WHEN** analyzing legacy projects, identifying architectural issues, and automatically restructuring them with best practices.
---

# Skill: refactor-arch

You are an expert software architect performing an automated architectural audit and refactoring. Follow the three phases below **in strict order**. Do not skip phases or merge them.

All reference knowledge lives in the `references/` directory alongside this SKILL.md. Load them as instructed per phase.

The references are split in two layers:

- **Stack-agnostic core** — `01-project-analysis.md`, `02-antipattern-catalog.md`, `03-report-template.md`, `04-architecture-guidelines.md`, `05-refactor-playbook.md`. These describe *what* to detect, *what* MVC means, and *what* transformations to apply, in concepts not in code.
- **Stack adapters** — `references/stack-adapters/<stack>.md`. These describe *how* the concepts manifest in a specific language (concrete syntactic signals, idiomatic file layout, before/after code per playbook entry, boot commands).

After Phase 1 detects the stack, you MUST load the matching adapter (e.g., `references/stack-adapters/python.md` for Python projects) and consult it alongside the core references for every subsequent phase. If no adapter exists for the detected stack, proceed using only the core references and record `Adapter: none — using agnostic signals only` in the Phase 1 output.

---

## PHASE 1 — PROJECT ANALYSIS

**Goal:** Detect the stack and map the current architecture. No file modifications allowed in this phase.

**Steps:**

1. Read `references/01-project-analysis.md` for detection heuristics.
2. After identifying the language, attempt to load `references/stack-adapters/<stack>.md` (e.g., `python.md` for Python, `nodejs.md` for Node.js). Record whether the adapter was loaded — this drives Phase 2 and Phase 3.
3. Scan the project directory:
   - Look for `package.json`, `requirements.txt`, `pyproject.toml`, `Pipfile`, `go.mod`, `pom.xml` to identify language and framework.
   - Read the entry point file (`app.py`, `index.js`, `main.py`, `server.js`, or equivalent).
   - List all source files and count lines of code per file.
   - Identify database layer (ORM, raw SQL, driver).
   - Identify existing directory structure (models/, routes/, controllers/, services/, etc.).
   - Read `api.http` if present — record all endpoints (method + path + sample payload).
4. Infer the application domain from route names, table names, and file names.
5. Print the Phase 1 banner **exactly** in this format:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <detected language>
Framework:     <framework + version>
Dependencies:  <key dependencies>
Domain:        <inferred domain description>
Architecture:  <current architecture description>
Source files:  <N> files analyzed
DB layer:      <ORM name or "raw SQL" or "none detected">
DB tables:     <comma-separated table names if found>
Endpoints:     <N> endpoints found in api.http
Adapter:       <path to loaded stack adapter, or "none — using agnostic signals only">
================================
```

6. Proceed automatically to Phase 2.

---

## PHASE 2 — ARCHITECTURE AUDIT

**Goal:** Find all issues in the codebase and produce a structured report. No file modifications allowed in this phase.

**Steps:**

1. Read `references/02-antipattern-catalog.md` to load the abstract detection catalog.
2. If a stack adapter was loaded in Phase 1, also consult `references/stack-adapters/<stack>.md` for each anti-pattern — the adapter has the concrete syntactic signals for the active language. The catalog's Concept + Semantic Signals remain authoritative; the adapter sharpens the match.
3. Read `references/03-report-template.md` to load the report format.
4. For each source file, scan for every anti-pattern in the catalog. Record:
   - The exact file path and line range where the pattern was found.
   - The severity (CRITICAL / HIGH / MEDIUM / LOW).
   - A concrete description of what was found (not generic — reference the actual code).
5. Sort all findings in that order: CRITICAL, HIGH, MEDIUM, LOW
6. Print the full audit report following the template in `references/03-report-template.md`.
7. Save the report to `../z_reports/audit-project-<name>.md` relative to the project root (create the `z_reports/` directory if it does not exist — but at the **workspace root**, not inside the project).

**MANDATORY STOP — do not proceed without explicit confirmation:**

Print this exact line and wait for user input:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- If the answer is `n` or anything other than `y`: print "Refactoring cancelled. Audit report saved." and stop.
- If the answer is `y`: proceed to Phase 3.

---

## PHASE 3 — REFACTORING + VALIDATION

**Goal:** Restructure the project to MVC, eliminate identified issues, validate the application still works.

**Steps:**

1. Read `references/04-architecture-guidelines.md` for the abstract MVC structure and layer responsibilities.

2. Read `references/05-refactor-playbook.md` for the conceptual transformation steps per anti-pattern.

3. If a stack adapter was loaded in Phase 1, consult `references/stack-adapters/<stack>.md § Layout` for the idiomatic file naming/extensions, and `§ PB-XX` for the concrete before/after code in the active language. The core playbook describes *what* to do; the adapter shows *how* to write it.

4. Read `api.http` (already loaded in Phase 1) to know which endpoints must remain working after refactoring.

5. Plan the full transformation before touching any file:
   - Map each existing file to its target location in the MVC structure.
   - List which anti-patterns will be fixed and by which playbook pattern.

6. Execute transformations **one domain at a time** (e.g., finish all task-related files before moving to users):
   - Create the new directory structure first (following the adapter's `§ Layout` when available).
   - Move / rewrite files according to the playbook.
   - Create environment variable file listing every environment variable extracted from hardcoded values.
   - Never delete the original entry point. adapt it as the composition root.

7. **Validation — mandatory after all changes:**
   a. Verify project README.md for any manual setup instructions (e.g., environment variables, database initialization, seed scripts).
   b. Install dependencies if needed (the adapter's `§ Boot & Validation` section lists the canonical commands for the stack).
   c. Start the application.
   d. Wait for the server to be ready (poll with `curl -s http://127.0.0.1:<port>/` or a known endpoint until it responds).
   e. For **each request** found in `api.http`, execute it with `curl` and verify:
      - HTTP status code is 2xx (or the same code as before refactoring for expected errors).
      - Response body contains expected fields (check top-level keys, not exact values).
   f. Stop the background server.
   g. Save the summary at `../z_reports/refactor-project-<name>.md`:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<print the actual new directory tree>

## Fixes Applied
<list each anti-pattern fixed with the playbook pattern used>

## Validation
<one line per endpoint from api.http>
  ✓ GET /tasks → 200 OK
  ✓ POST /tasks → 201 Created
  ...

## Environment Variables
  Created: <environment_variable_file>
  Variables: <list>
================================
```

8. If any validation step fails: print the failure clearly, do not mark it as ✓, and suggest the fix without modifying more files automatically.
