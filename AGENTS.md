# AGENTS.md
Guide for coding agents in `/home/kdresdell/Documents/DEV/minipass_env`.
Prefer the most local instructions when rules conflict.

## Read This First
- `app/CLAUDE.md` for work inside `app/` (strict UI + email rules).
- `MinipassWebSite/CLAUDE.md` for work inside `MinipassWebSite/`.
- Root `CLAUDE.md` is useful for infra context, but parts are stale (for tests/migrations prefer code and this file).

## Repository Shape (Important)
- `app/` is a Git submodule (`.gitmodules` points to `git@github.com:windseeker5/dpm.git`); treat it as its own project boundary.
- `app/` is the main Flask SaaS app (`app/app.py`) with SQLite at `app/instance/minipass.db`.
- `MinipassWebSite/` is a separate Flask app (`MinipassWebSite/app.py`) with its own SQLite DB (`MinipassWebSite/customers.db`).
- Root `docker-compose.yml` runs shared infra (nginx proxy, acme companion, mailserver, controller proxy).

## Setup + Run
Main app:
```bash
cd app
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Website app:
```bash
cd MinipassWebSite
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Infra from repo root:
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f mailserver
```

## Validation Commands (No Repo-Wide Lint/CI Config Found)
- Use compile checks + focused tests; there is no `pytest.ini`, `tox.ini`, `Makefile`, pre-commit, or GitHub workflow in this repo.

Main app syntax checks:
```bash
cd app
source venv/bin/activate
python -m py_compile app.py utils.py models.py api/settings.py decorators.py
python -m compileall .
```

Website syntax check:
```bash
cd MinipassWebSite
source venv/bin/activate
python -m compileall .
```

Website tests:
```bash
cd MinipassWebSite
source venv/bin/activate
python -m unittest discover -s tests -p "test_*.py" -v
```

## Testing Gotchas
- The commonly documented `app` unittest target `test.test_kpi_data` is stale (file is absent).
- `app/pytest/` currently has no `test_*.py` suite; it mostly contains scripts.
- `app/test/` contains utility scripts and assets, not a standard unit-test package.
- Some scripts trigger real email and/or deployment actions (for example `MinipassWebSite/utils/test_deployment.py`); do not run these as routine verification.

## Database + Migration Workflow
- For `app/` schema changes: edit `app/models.py` and update `app/migrations/upgrade_production_database.py` (idempotent).
- Even though `Flask-Migrate` is initialized in `app/app.py`, local project guidance says not to rely on `flask db migrate` for this workflow.
- In `MinipassWebSite/`, direct `sqlite3` patterns are standard.

## High-Impact Local Conventions
- `app/app.py` and `app/utils.py` are very large; avoid formatting-only churn.
- Main app UI must follow Tabler patterns from `app/docs/DESIGN_SYSTEM.md`; avoid ad hoc CSS/JS frameworks.
- For email changes in `app/`, read `app/docs/EMAIL_TEMPLATE_SYSTEM.md` and `app/docs/EMAIL_DELIVERABILITY.md` first.
