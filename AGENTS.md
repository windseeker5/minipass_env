# AGENTS.md
Guide for coding agents in `/home/kdresdell/Documents/DEV/minipass_env`.
Prefer the most local instructions when rules conflict.

## Rule Sources
- `app/CLAUDE.md` for `app/`.
- Root `CLAUDE.md` for repo-wide infra context.
- `MinipassWebSite/CLAUDE.md` for `MinipassWebSite/`.
- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` were found.

## Setup Commands
### Main app
```bash
cd app
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
- Main DB: `app/instance/minipass.db`.
- Docs say dev server usually runs on `localhost:5000`.

### MinipassWebSite
```bash
cd MinipassWebSite
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Infrastructure
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f mailserver
```

## Build / Lint / Validation
- No repo-wide formatter or linter is configured.
- Prefer syntax checks plus targeted tests.

Main app syntax check:
```bash
cd app
source venv/bin/activate
python -m py_compile app.py utils.py models.py api/settings.py decorators.py
```

Main app compile sweep:
```bash
cd app
source venv/bin/activate
python -m compileall .
```

Website compile sweep:
```bash
cd MinipassWebSite
source venv/bin/activate
python -m compileall .
```

## Test Commands
### Main app
- Older docs still mention `python -m unittest test.test_kpi_data -v`.
- That path is stale; `app/test/test_kpi_data.py` does not exist.
- Current tests/scripts live mainly in `app/pytest/`.

Run a single unittest file:
```bash
cd app
source venv/bin/activate
python -m unittest discover -s pytest -p "test_subscription_settings.py" -v
```

Run all discoverable `app/pytest` unittests:
```bash
cd app
source venv/bin/activate
python -m unittest discover -s pytest -p "test_*.py" -v
```

Run a script-style test directly:
```bash
cd app
source venv/bin/activate
python pytest/test_all_email_templates.py
```

### MinipassWebSite
Run a single unittest file:
```bash
cd MinipassWebSite
source venv/bin/activate
python -m unittest discover -s tests -p "test_stripe_settings_deployment.py" -v
```

Run all website tests:
```bash
cd MinipassWebSite
source venv/bin/activate
python -m unittest discover -s tests -p "test_*.py" -v
```

### Current test caveats
- `app/pytest/test_subscription_settings.py` currently fails because several mocked targets no longer exist.
- `MinipassWebSite/tests/test_stripe_settings_deployment.py` mostly passes, but one assertion expects 6 settings while the code now writes 7 for empty/beta values.
- Some email-related scripts send real email; verify before running them, and do not assume existing red tests were caused by your change.

## Database / Migration Rules
### Main app
- Models live in `app/models.py`.
- `app/app.py` initializes Flask-Migrate, but `app/CLAUDE.md` says not to use Flask-Migrate for schema changes in this workflow.
- For schema changes: update `app/models.py`, then update `app/migrations/upgrade_production_database.py`, and keep the upgrade script idempotent.

### MinipassWebSite
- Direct `sqlite3` usage is normal in `MinipassWebSite/app.py` and `MinipassWebSite/utils/`.
- Prefer `with sqlite3.connect(...) as conn:` when touching those helpers.

## Code Style
### General
- Follow the surrounding style of the touched file.
- Keep changes small and local.
- Preserve existing behavior unless the task requires changing it.
- Add comments only when the code intent is not obvious.

### Imports
- Prefer standard library, third-party, then local imports.
- Do not churn giant legacy import blocks for style only.
- Preserve lazy imports inside routes/helpers when they avoid cycles or heavy startup cost.

### Formatting
- Use 4-space indentation.
- Match the file’s existing quote style and spacing.
- Avoid formatting-only diffs in very large files like `app/app.py` and `app/utils.py`.

### Types
- The repo is mixed-typed.
- Newer modules, especially `app/chatbot_v2/`, use type hints and dataclasses.
- Add type hints in new helpers, new modules, and tests when they clearly help.
- Do not retrofit exhaustive typing into legacy monolith files unless required.

### Naming
- `snake_case` for functions, variables, and route handlers.
- `PascalCase` for classes and SQLAlchemy models.
- `UPPER_SNAKE_CASE` for constants and config maps.
- Keep DB setting names exact, including all-caps keys like `MINIPASS_TIER`.

### Error handling
- Prefer specific exceptions over `except Exception` in new code.
- For Flask write paths, rollback `db.session` before returning an error after failed writes.
- Log useful context with `logger.error(...)` or `subscription_logger.error(...)`.
- Return structured JSON errors for API routes.
- Use `flash(...)` for user-facing server-rendered admin flows.
- Do not silently swallow exceptions unless the failure is intentionally non-fatal.

### Database access
- In `app/`, use SQLAlchemy models and established `db.session` patterns.
- In `MinipassWebSite/` and many tools, direct `sqlite3` access is expected.
- Commit explicitly after writes.

### Templates / frontend
- Main app templates must follow Tabler.io patterns.
- Read `app/docs/DESIGN_SYSTEM.md` before non-trivial UI work.
- `app/CLAUDE.md` says no React, Vue, or Angular.
- Keep business logic in Python, not JavaScript.
- Keep JS small and focused on lightweight UI interactions.
- Avoid ad hoc custom CSS or `<style>` blocks in the main app unless the design docs explicitly require an existing documented pattern.

### Email / security
- Read `docs/EMAIL_TEMPLATE_SYSTEM.md` and `docs/EMAIL_DELIVERABILITY.md` before changing email code.
- Be careful with real recipients and real send paths.
- Preserve sanitization and hosted-image/CID behavior when editing email templates.
- Never hardcode secrets.
- Use environment variables and existing settings tables.
- Preserve CSRF, session, CSP, and sanitization already in place.
