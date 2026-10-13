# Local setup and SQLite-to-MySQL guide

Run application commands from `backend/`. MySQL must be installed, running, and configured before migrations or server startup.

## Install and configure MySQL

Check for an existing installation before installing:

```bash
mysql --version
brew services list | grep -i mysql
```

If MySQL is missing, install and start it with Homebrew:

```bash
brew install mysql
brew services start mysql
```

If already installed but stopped, start the existing service with `brew services start mysql`. Check connectivity with `mysqladmin ping --host=127.0.0.1 --port=3306 --user=root --password`; the password option prompts securely.

Connect as a MySQL administrator, then create the project's database and a restricted local application user. Replace the example password before executing:

```bash
mysql --host=127.0.0.1 --user=root --password
```

```sql
CREATE DATABASE research_portal
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
CREATE USER 'research_portal_app'@'127.0.0.1'
  IDENTIFIED BY 'replace-with-a-strong-local-password';
GRANT ALL PRIVILEGES ON research_portal.* TO 'research_portal_app'@'127.0.0.1';
```

The Django configuration is in `backend/config/settings.py`. It uses the MySQL backend and reads `DJANGO_DB_NAME`, `DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`, `DJANGO_DB_HOST`, and `DJANGO_DB_PORT` from the environment. `utf8mb4` is configured for the connection; the database uses `utf8mb4_unicode_ci`.

## Install Python dependencies and run

From the repository root:

```bash
cd backend
test -f .env || cp .env.example .env
# Edit .env: enter the database username/password and a private DJANGO_SECRET_KEY.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
set -a
source .env
set +a
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The settings module reads environment variables but does not parse `.env` itself; the `source` commands export values into the current shell. Generate a secret key with `python -c "import secrets; print(secrets.token_urlsafe(50))"`. The real `.env` is ignored by Git. On macOS, if `mysqlclient` compilation fails due to a missing `pkg-config`, install `brew install pkgconf`, then repeat `pip install -r requirements.txt`.

## Safely transfer data from SQLite to a new MySQL database

This procedure is only for importing a SQLite source into a **separate, empty** MySQL schema. Do not repeat the fixture import into an already-populated target. The application’s current SQLite database and backup should remain untouched until record counts, relationships, login, and workflows are checked.

1. Back up SQLite and check its migration history:

```bash
cd backend
umask 077
cp -p ../db.sqlite3 "../db.sqlite3.before-mysql-$(date +%Y%m%d%H%M%S)"
export DJANGO_DB_ENGINE=django.db.backends.sqlite3
export DJANGO_DB_NAME="$PWD/../db.sqlite3"
python manage.py showmigrations --plan
```

Confirm the source's original schema migrations are applied before exporting. The new `accounts.0001` and `opportunities.0003` migrations are a model-state/content-type transition for this refactor; leave them unapplied on the preserved SQLite source if it must remain unchanged. They do not create, drop, or alter the physical profile table. Export related records using Django's natural foreign keys, excluding generated content types, permissions, and transient records:

```bash
python manage.py dumpdata \
  --database default \
  --natural-foreign \
  --natural-primary \
  --exclude contenttypes \
  --exclude auth.permission \
  --exclude admin.logentry \
  --exclude sessions.session \
  --indent 2 > /tmp/research-opportunity-portal-data.json
unset DJANGO_DB_ENGINE DJANGO_DB_NAME
```

The fixture contains user data and password hashes. Keep the restrictive `umask`, do not put it in the repository, and remove it once the import is verified.

2. Configure the empty MySQL database and load its environment from `backend/.env`:

```bash
set -a
source .env
set +a
python manage.py check
python manage.py migrate
```

Do not delete migration files, reset migration history, or use `--fake` to bypass errors. Migrations create the target schema, not the source data.

3. Import and verify the fixture:

```bash
python manage.py loaddata /tmp/research-opportunity-portal-data.json
python manage.py shell -c "from django.contrib.auth.models import User; from accounts.models import UserProfile; from opportunities.models import Department, Opportunity; print('users:', User.objects.count(), 'profiles:', UserProfile.objects.count(), 'departments:', Department.objects.count(), 'opportunities:', Opportunity.objects.count())"
```

Compare counts with the SQLite source and inspect key profile, department, and opportunity ownership relationships. Django migrations create current content types and permissions. This project's profile-app migration preserves the existing `opportunities_userprofile` table and moves its `UserProfile` content type, so historical rows and assigned profile permissions remain associated. Then test teacher and student login, dashboards, and opportunity creation/visibility. Keep the source SQLite and backup until these checks pass.

After successful verification, remove the private temporary fixture:

```bash
rm /tmp/research-opportunity-portal-data.json
```

## Tests and troubleshooting

With MySQL configured and `.env` sourced, from `backend/` run:

```bash
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
python manage.py test accounts dashboard opportunities
```

MySQL tests create and drop a separate test schema. If the scoped application account cannot do so, run tests with a local test-only database account that has appropriate create/drop permissions. Do not grant those extra privileges to a production runtime account.

- **Connection refused:** start MySQL and confirm host/port with `mysqladmin ping`.
- **Access denied:** verify username, password, and account host (`127.0.0.1` and `localhost` are distinct in MySQL).
- **Unknown database:** create `research_portal` before running migrations.
- **Test schema permission error:** use a local test-only account allowed to create and drop the test schema.
- **CSRF or login issue:** keep the same host and port from login through form submission; do not disable CSRF middleware.
- **Templates/static files missing:** confirm `backend/templates/` and `backend/static/` are present and use `python manage.py runserver` from `backend/`.

Local `.env` files, SQLite databases, and dumps are private and must never be committed.
