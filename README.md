# University Research Opportunity Portal

A Django website and REST API for publishing university research opportunities. Teachers manage their own opportunities, students browse eligible open opportunities, and administrators manage portal records.

## Project layout

```text
research-opportunity-portal/
├── backend/
│   ├── config/          # Django settings and root URL/ASGI/WSGI configuration
│   ├── accounts/        # Registration, login/logout, profiles, and account API
│   ├── opportunities/   # Opportunity and department models, forms, views, API, migrations
│   ├── dashboard/       # Teacher, student, and administrator dashboards
│   ├── templates/       # Shared Django HTML templates
│   ├── static/          # CSS, JavaScript, and images
│   ├── .env.example     # Placeholder configuration (copy to ignored .env)
│   ├── manage.py        # Django command-line entry point
│   └── requirements.txt # Python dependencies
├── docs/
│   ├── project_structure.md
│   └── setup_guide.md
├── postman/
├── .gitignore
├── LICENSE
└── README.md
```

`backend/` contains the complete Django application. `config/` controls Django settings and URL routing. `accounts/`, `opportunities/`, and `dashboard/` separate the three main responsibilities. The templates and static assets are served by Django; no separate frontend server or framework is required. Database models and migrations are the source of truth for stored records.

## Requirements

- Python 3.13 (see the pinned Django version in `backend/requirements.txt`)
- MySQL 8.0+ or a Django-supported MariaDB version
- macOS users need Homebrew only if MySQL is not already installed

## Setup on macOS

### 1. Check or start MySQL

Check before installing so an existing database installation is not replaced:

```bash
mysql --version
brew services list | grep -i mysql
```

If MySQL is not installed:

```bash
brew install mysql
brew services start mysql
```

If it is installed but stopped, start the existing service:

```bash
brew services start mysql
mysqladmin ping --host=127.0.0.1 --port=3306 --user=root --password
```

The `--password` flag prompts securely. Do not assume the MySQL administrator password is empty.

### 2. Create a database and application user

Connect using a MySQL administrator account:

```bash
mysql --host=127.0.0.1 --user=root --password
```

Then run the following SQL, replacing the example password with a strong private password:

```sql
CREATE DATABASE research_portal
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
CREATE USER 'research_portal_app'@'127.0.0.1'
  IDENTIFIED BY 'replace-with-a-strong-local-password';
GRANT ALL PRIVILEGES ON research_portal.* TO 'research_portal_app'@'127.0.0.1';
```

Use this restricted application user for local runtime access, not the MySQL administrator account.

### 3. Configure environment and install dependencies

From the repository root:

```bash
cd backend
test -f .env || cp .env.example .env
# Edit .env and set DJANGO_DB_USER, DJANGO_DB_PASSWORD and DJANGO_SECRET_KEY.
# Keep this file private; it is excluded from Git.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
set -a
source .env
set +a
```

The Django settings read credentials from environment variables; Django does not load `.env` automatically. Generate a local secret key with `python -c "import secrets; print(secrets.token_urlsafe(50))"` and put the result in `.env`. On macOS, if `mysqlclient` fails to build because `pkg-config` is unavailable:

```bash
brew install pkgconf
python -m pip install -r requirements.txt
```

### 4. Migrate and run

MySQL must be running and configured before applying migrations:

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to sign in, `/register/` to register a student or teacher, `/opportunities/` to browse, and `/admin/` for Django Admin. Add departments in the admin before registering teachers. Keep the same hostname and port during login and form submissions so session and CSRF cookies remain valid.

## Database migration and preservation

Changing the configured backend creates the schema in MySQL; it does not copy SQLite records. Before migrating an existing project, back up its SQLite database, confirm migrations are applied to the source, create a separate empty MySQL schema, apply migrations there, then transfer fixture data and verify counts/relationships. Never run `loaddata` against a database that already contains the source records. Keep the SQLite database and backup until MySQL authentication and application workflows are verified. Detailed commands are in [docs/setup_guide.md](docs/setup_guide.md).

This repository's local MySQL database was populated from the existing SQLite database and verified with 7 users, 4 profiles, 1 department, and 1 opportunity. The SQLite source was retained. The `accounts` app split preserves the existing physical `opportunities_userprofile` table through state-only migrations; do not delete or rewrite the historical migrations.

## Tests and checks

Activate the virtual environment and load `backend/.env`, then from `backend/` run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py test accounts dashboard opportunities
```

The MySQL test runner needs an account that can create and drop a separate test database. The scoped runtime account may not have that permission; use a suitable local test account only for test runs, never as the production runtime account.

## GitHub safety

The root `.gitignore` excludes real `.env` files, database files, virtual environments, uploaded media, and generated Python files. Review `git status --short` and `git diff --cached --name-only` before committing. Do not upload credentials, local SQLite files, database dumps, or the real `.env`. To publish, create or select the intended GitHub repository, add its remote, then push the reviewed branch:

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/research-opportunity-portal.git
git push -u origin main
```

Only add the remote if one is not already configured and you have confirmed it is the correct repository.
