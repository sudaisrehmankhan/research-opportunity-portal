# University Research Opportunity Portal

A Django web application and REST API for sharing university research projects. Students can discover open opportunities, and teachers can manage opportunities in their department. Administrators manage users, profiles, departments, and all opportunities.

## The problem it solves

Research opportunities are often spread across departments, faculty pages, and informal messages. This portal brings opportunities into one searchable place and gives each role the tools and permissions needed to manage or find research work.

## Features

### Students

- Register with student details and sign in.
- View a student dashboard and update their profile.
- Browse and search opportunities, filter by status or department, and view full details.
- Read access only; students cannot create, edit, or delete opportunities.

### Teachers

- Register with a department and faculty details and sign in.
- View a teacher dashboard and update their profile.
- Create opportunities for their registered department.
- Edit, close/reopen, or delete opportunities they own.
- Teachers cannot modify another teacher's opportunities.

### Administrators

- Use Django Admin and the portal admin dashboard.
- Manage users, teacher/student profiles, departments, and all opportunities.

### API and validation

- CRUD API for opportunities, with public read access and authenticated writes.
- Search, department/status filters, ordering, and pagination.
- Validates required fields, position counts, status values, department membership, and future deadlines for open opportunities.
- Postman collection includes create/list/detail/update/delete, invalid input, unauthenticated write, and deleted-record checks.

## Technology stack

- Python and Django
- Django REST Framework
- SQLite for local development; MySQL configuration for deployments
- HTML, CSS, and JavaScript using the Fetch API
- Postman collection for API checks

## Project structure

```text
research-opportunity-portal/
├── config/                 # Django settings and root URL configuration
├── frontend/
│   ├── templates/          # Login, registration, dashboards, profiles, detail pages
│   ├── index.html          # Opportunity listing and teacher management UI
│   ├── script.js           # Fetch API and frontend interactions
│   └── style.css
├── opportunities/
│   ├── migrations/         # Database schema migrations
│   ├── admin.py
│   ├── forms.py
│   ├── models.py           # Departments, profiles, opportunities
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── postman/
│   └── research-opportunity-portal.json
├── .env.example
├── .gitignore
├── manage.py
└── requirements.txt
```

The local `db.sqlite3`, `.env`, and virtual environment are intentionally not part of the repository.

## Prerequisites

- Python 3.13 (or a compatible Python version supported by the pinned Django release)
- macOS Terminal or another shell
- MySQL Server only if choosing MySQL instead of the default SQLite database

## Setup and run locally

From the project root:

```bash
cd /Users/sudaiskhan/Desktop/research-opportunity-portal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Generate a fresh development secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Replace the sample `DJANGO_SECRET_KEY` in `.env` with the generated value. Load the environment file into the current terminal session:

```bash
set -a
source .env
set +a
```

Create the database schema and an administrator:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Run the app:

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the login page. Public opportunity browsing is at `http://127.0.0.1:8000/opportunities/`; Django Admin is at `http://127.0.0.1:8000/admin/`.

## First-time portal configuration

1. Sign in to Django Admin with the superuser created above.
2. Add one or more departments under **Opportunities → Departments**.
3. Register a teacher and a student at `/register/`. Teacher accounts must choose a department; student accounts must provide a student number.
4. Sign in as the teacher, create an opportunity for that teacher's department, and test edit/status/delete actions.
5. Sign in as the student and confirm that opportunity browsing and details are available, while management controls are not.
6. Use the superuser account to manage all records from Django Admin and the admin dashboard.

Accounts created through public registration cannot become administrators. Administrators are created with `createsuperuser` or managed in Django Admin.

## Environment variables

`.env.example` documents the supported settings. `.env` is for local values and is ignored by Git.

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django signing key; set a unique value | Local-only fallback when debug is on |
| `DJANGO_DEBUG` | Enables Django debug mode when set to `1` | `1` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed host names | `localhost,127.0.0.1,[::1]` |
| `DJANGO_DB_ENGINE` | Django database backend | SQLite |
| `DJANGO_DB_NAME` | Database name or SQLite file path | `db.sqlite3` in the project root |
| `DJANGO_DB_USER` | Database user | Empty |
| `DJANGO_DB_PASSWORD` | Database password | Empty |
| `DJANGO_DB_HOST` | Database host | Empty |
| `DJANGO_DB_PORT` | Database port | Empty |

Never commit `.env`, database passwords, production keys, or user data. Production deployments must set a private `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=0`, configure `DJANGO_ALLOWED_HOSTS`, and use HTTPS.

## MySQL setup (optional)

Install the declared dependencies, create a database, and put MySQL settings in your local `.env`:

```bash
mysql -u root -p -e "CREATE DATABASE research_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Set these values in `.env` (do not commit the real username or password):

```dotenv
DJANGO_DB_ENGINE=django.db.backends.mysql
DJANGO_DB_NAME=research_portal
DJANGO_DB_USER=your_local_mysql_user
DJANGO_DB_PASSWORD=your_local_mysql_password
DJANGO_DB_HOST=127.0.0.1
DJANGO_DB_PORT=3306
```

Reload `.env` in the terminal using the `set -a; source .env; set +a` commands above, then apply migrations with `python manage.py migrate`.

## API endpoints

| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/opportunities` | Public |
| POST | `/api/opportunities` | Teacher or admin |
| GET | `/api/opportunities/<id>` | Public |
| PUT | `/api/opportunities/<id>` | Owner teacher or admin |
| DELETE | `/api/opportunities/<id>` | Owner teacher or admin |
| GET | `/api/departments/` | Public |
| POST | `/api/departments/` | Admin |
| GET/PATCH | `/api/profile/` | Authenticated account's own profile |

Opportunity list query parameters include `search`, `status`, `department`, `ordering`, and `page`. Pagination returns six opportunities per page.

## Automated tests

With the virtual environment activated and dependencies installed:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The suite covers opportunity CRUD, ownership/role permissions, validation, registration, login errors, successful role login, logout, protected-page access, and session/back-navigation behavior.

## Screenshots

No screenshots are currently included. Add appropriately anonymized screenshots here when available; do not include personal data or real user account details.

## Known limitations and future improvements

- SQLite is the local default. MySQL requires a separate server/database and environment configuration.
- There is no application-submission workflow, email notification service, or password-reset email configuration.
- Registration supports students and teachers; administrator accounts must be provisioned by an existing administrator or with Django's `createsuperuser` command.
- Future improvements could include opportunity applications, email deadline reminders, deployment automation, and additional accessibility/browser testing.

## Postman

Import `postman/research-opportunity-portal.json` into Postman. Configure its `base_url`, `username`, and `password` variables for a registered teacher account, and create the selected department in Django Admin before sending opportunity creation requests.

## GitHub repository setup (macOS)

The local project directory may not yet have Git history. These commands initialize it without uploading the local database or environment file:

```bash
cd /Users/sudaiskhan/Desktop/research-opportunity-portal
git status --short --branch
git init -b main
git add .
git status --short
git diff --cached --name-only
git diff --cached --check
git check-ignore -v .env db.sqlite3 venv/
```

Review the staged file list. It should include source, templates, migrations, docs, the Postman collection, and configuration examples. It must not include `.env`, `db.sqlite3`, `venv/`, `.venv/`, or uploaded private files. If any private or unexpected file appears, unstage it and fix `.gitignore` before continuing:

```bash
git restore --staged path/to/unwanted-file
```

Create the initial commit:

```bash
git commit -m "Prepare research opportunity portal for GitHub"
```

On GitHub, create a new empty repository named `research-opportunity-portal` (do not initialize it with a README, license, or `.gitignore`, since these already exist locally). Replace `YOUR_GITHUB_USERNAME` below with your GitHub username:

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/research-opportunity-portal.git
git remote -v
git push -u origin main
```

If `git remote add` reports that `origin` already exists, inspect it with `git remote -v` and do not replace it until you confirm it is the intended repository. Do not force-push or overwrite existing history. The project is not uploaded until `git push` succeeds and the repository is visible at the intended GitHub URL.

### Future updates

```bash
git status
git add .
git status
git diff --cached --check
git commit -m "Describe the change"
git push
```

`git status` shows changed and staged files. Review it before staging and again before committing so that `.env`, local databases, credentials, and private user data are not accidentally uploaded. `git add .` stages changes; `git commit` saves them in local Git history; `git push` publishes committed changes to GitHub. Never blindly stage or commit sensitive files.
