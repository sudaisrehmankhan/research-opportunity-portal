# Project structure

The project keeps Django, templates, and static assets together under `backend/` so it can be run with one server and a small number of folders.

## Django project

- `backend/manage.py` is the Django command-line entry point.
- `backend/config/` contains settings, root URLs, and ASGI/WSGI entry points.
- `backend/accounts/` handles registration, authentication, profiles, serializers, and account administration.
- `backend/opportunities/` owns department and research opportunity models, forms, browser/API views, URLs, admin, tests, and migrations.
- `backend/dashboard/` selects and displays the teacher, student, and administrator dashboards.
- `backend/templates/` contains the shared HTML templates and small reusable template partials.
- `backend/static/` contains stylesheets, JavaScript, and images.
- `backend/requirements.txt` declares Python dependencies; `backend/.env.example` shows the environment variables without real credentials.

## Database and migration history

The project uses MySQL through Django's MySQL backend. Profiles are now an `accounts` model, but the model explicitly retains its existing physical table name, `opportunities_userprofile`. The first accounts migration adds the model to Django's migration state without creating or replacing that table and moves the existing profile content type. The following opportunities migration removes the old model from the opportunities migration state only. These migrations preserve existing profile records, foreign keys, and profile permissions. Do not rewrite the already-applied migrations or remove those compatibility migrations.

## Local-only files

`.gitignore` excludes environment secrets, SQLite database files, virtual environments, generated static files, caches, and operating-system files. Keep database exports and local backups out of Git. The HTML pages are rendered by Django; no separate frontend server is used.
