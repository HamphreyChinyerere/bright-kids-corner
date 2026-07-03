# Bright Kids Corner

This project is configured for deployment on Render with a linked PostgreSQL database.

## Render deployment

The repository includes `render.yaml`, which defines:
- a Python web service using `gunicorn`
- a free-tier Render PostgreSQL database service
- `buildCommand` that installs requirements and runs `collectstatic`
- `releaseCommand` that runs migrations on deploy

## Required Render environment variables

Render automatically injects `DATABASE_URL` for linked Postgres databases in the same project.

In the Render service settings, add:
- `DJANGO_SECRET_KEY` — a strong random secret key for production
- `DJANGO_DEBUG` = `False`
- `DJANGO_ALLOWED_HOSTS` = `*`

Optional:
- `DJANGO_TRUSTED_ORIGINS` = `https://your-app.onrender.com` or a comma-separated list of trusted domains

## Python runtime

This project includes `runtime.txt`, which configures Python 3.11 on Render.

## Local notes

The local Windows environment may not run `gunicorn` successfully because it depends on POSIX-only modules like `fcntl`. Use the Render deployment or a Linux/WSL environment for production-like testing.

Local development and change log
-------------------------------

This repository includes a `CHANGELOG.md` file at the project root where local, manual changes and diagnostic actions will be recorded by the maintainer or contributors. When working locally, record any manual fixes, migrations, environment changes, or dependency adjustments in `CHANGELOG.md` so others can reproduce the steps.

If you need a quick local checklist:

- Ensure dependencies are installed: `python -m pip install --user -r requirements.txt`
- Apply migrations: `python manage.py migrate`
- Run server: `python manage.py runserver`

