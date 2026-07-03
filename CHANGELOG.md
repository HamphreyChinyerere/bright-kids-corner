# CHANGELOG

All local changes and diagnostic actions will be recorded here.

## 2026-07-03 — Initial local log

- Created changelog and appended local development notes to `README.md`.
- Identified missing `django` package and installed local runtime dependencies.
- Installed minimal runtime packages to avoid `psycopg2-binary` build issues on Windows.
- Started development server with `DJANGO_DEBUG=True` for local testing.
- Observed `OperationalError: no such table: auth_user` during login; will apply migrations.
 
## 2026-07-03 17:45 UTC — Migrations applied

- Ran `python manage.py migrate` with `DJANGO_DEBUG=True` and applied migrations for: `admin`, `auth`, `contenttypes`, `core`, `sessions`.

Next steps:

- Restart or continue the development server (it may already be running). Attempt the login flow again.
- Added a particle background effect for the auth page: created `static/particles/particle-terms.js`, `particle-system.js`, and `particle-styles.css`, and included them in `templates/auth.html`.
- Particle system uses a max active particle counter of 20 and supports hover pause/resume; terms are grouped by subject in `particle-terms.js`.

- Added console debug logs to `core/static/particles/particle-terms.js` and `core/static/particles/particle-system.js` to help verify asset loading in the browser console.


