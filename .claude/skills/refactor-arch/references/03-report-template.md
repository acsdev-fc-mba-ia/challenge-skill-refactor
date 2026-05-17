# Audit Report Template

Use this exact format for the Phase 2 output. Fill in every placeholder. Do not omit sections.

---

## Report Format

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project directory name>
Stack:   <Language> + <Framework version>
Files:   <N> analyzed | ~<total LOC> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>
Total findings: <n>

## Findings

### [CRITICAL] <Anti-pattern name from catalog>
File: <relative/path/to/file.py>:<line-start>-<line-end>
Description: <Concrete description — reference the actual variable name, function name, or code construct found. Never write generic descriptions.>
Impact: <One sentence on why this matters in production.>
Recommendation: <One actionable sentence on how to fix it.>

### [CRITICAL] <Next finding>
File: <path>:<lines>
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] <Anti-pattern name>
File: <path>:<lines>
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] <Anti-pattern name>
File: <path>:<lines>
Description: ...
Impact: ...
Recommendation: ...

### [LOW] <Anti-pattern name>
File: <path>:<lines>
Description: ...
Impact: ...
Recommendation: ...

================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Formatting Rules

1. **Order is mandatory:** CRITICAL → HIGH → MEDIUM → LOW. Within the same severity, order by file name alphabetically.
2. **`file:line` is mandatory** on every finding. Use `1-88` for a full file, `41-57` for a specific block.
3. **Descriptions must be concrete.** Bad: "There is a SQL injection vulnerability." Good: "Function `get_product()` at line 47 builds the SQL query as `'SELECT * FROM products WHERE id = ' + str(id)`, allowing arbitrary SQL injection."
4. **One finding per anti-pattern instance per file.** If the same anti-pattern appears in 3 files, write 3 separate findings.
5. **The confirmation prompt** (`Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`) must appear as the very last line of the printed output, after the closing banner.

---

## Example Finding (filled in correctly)

```
### [CRITICAL] Hardcoded Secrets / Credentials
File: app.py:13
Description: `SECRET_KEY` is assigned the literal string `"super-secret-key-123"` directly in app.py. The value is committed to version control and visible to anyone with repository access.
Impact: Any user with read access to the repo can forge session cookies and impersonate any authenticated user.
Recommendation: Move to `.env` as `SECRET_KEY=<generated value>` and load with `os.getenv('SECRET_KEY')`.
```

---

## Report Save Location

Save the report file at: `<workspace-root>/z_reports/audit-project-<project-name>.md`

- `<workspace-root>` is the parent directory of the project being audited (one level up from the project root).
- `<project-name>` is the project directory name (e.g., `code-smells-project`, `ecommerce-api-legacy`, `task-manager-api`).
- Create the `z_reports/` directory if it does not exist.
- The file content must be exactly what was printed to the terminal (the full report including the banner and findings).
