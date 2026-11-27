<p align="center">
  <img src="static/img/project-logo-transparent.svg" alt="SQL Playground logo" width="104" />
</p>

<h1 align="center">SQL Playground</h1>

<p align="center">
  <strong>Learn SQL by writing, running, and understanding real queries.</strong><br />
  An interactive SQL learning platform designed to help IT students develop their database querying skills.
</p>

<p align="center">
  <a href="https://www.djangoproject.com/"><img src="https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white" alt="Django 6.1" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12 or newer" /></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL on Supabase" /></a>
  <img src="https://img.shields.io/badge/status-active%20development-1F6BFF" alt="Active development" />
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#features">Features</a> ·
  <a href="#tech-stack">Tech Stack</a> ·
  <a href="#getting-started">Getting Started</a> ·
  <a href="#routes">Routes</a> ·
  <a href="#testing">Testing</a> ·
  <a href="#roadmap">Roadmap</a>
</p>

---

## Overview

SQL Playground is a web-based learning platform that allows IT students to practice SQL through interactive query writing and execution. Students follow guided lessons or open the free sandbox, write a query in the editor, run it, and see the results in the browser without installing a database server.

The project now covers the full learner flow: registration, login, role-based dashboards, profile management, auto-checked guided lessons, a free SQL sandbox, saved queries, and query history. Administrator functions are built into the project at `/dashboard/administrator/`; the Django admin site is not installed. Invalid or disallowed statements return a clear message, and every sandbox execution is recorded in the learner's query history.

## Features

### Guided Lessons
- Eight lessons across Beginner, Intermediate, and Advanced levels, from `SELECT` and `WHERE` to joins, `HAVING`, and subqueries.
- Each lesson states a task, gives a starter query and a hint, and checks the learner's result against a reference query.
- Order-sensitive lessons compare row order; other lessons accept the same rows in any order.
- Column aliases are ignored when grading, so learners can name aggregate columns the way the task asks.
- Progress and attempt counts are stored per learner, and completed lessons unlock a next-lesson link.
- Lesson checks run against the same isolated practice engine as the sandbox.

### SQL Sandbox
- Built-in School Database with `students`, `courses`, and `enrollments` tables, seeded automatically in an isolated SQLite database.
- Practice SQL never reaches application tables or the hosted PostgreSQL database.
- Schema viewer listing each table's columns and sample rows.
- SQL editor that runs one `SELECT` statement at a time; blank input, non-`SELECT` statements, write attempts, and multiple statements are rejected with a clear message.
- Results table with returned columns, rows, and row count, capped at 200 rows.
- Query timeout and row limits protect the request from slow or runaway queries.
- Query history showing the 10 most recent executions for the signed-in learner.
- Saved queries with create, view, edit, and delete, scoped to the owning learner.
- Editor contents and the last result are kept in the session so the workspace survives redirects.

### User Accounts
- Learner registration with required-field, email-format, unique username, unique email, and password-confirmation validation.
- Login using either a username or an email address.
- Remember me option that extends the session to 30 days.
- Secure password hashing with Django's standard password validators.
- Session-based authentication and protected routes.
- POST-only, CSRF-protected logout.

### Role-Based Dashboards
- Separate dashboards for Learners and Administrators.
- Server-side role-based access control on every dashboard view.
- Automatic Learner assignment during public registration.
- Superusers are always assigned the Administrator role.
- Learner dashboard shows completed lessons, saved queries, queries executed, lesson progress, and a link to the next lesson.

### Administrator User Management
- Account management inside the project at `/dashboard/administrator/users/`; the Django admin site is not installed.
- Search accounts by username, first name, last name, or email, and filter by role and active status.
- Paginated account list with role and status labels.
- Create accounts, update details and roles, activate or deactivate access, set a new password, and delete accounts after a confirmation step.
- Administrators cannot demote or deactivate their own account, delete their own account, or remove the last active administrator.

### Profile Management
- View and edit name, email address, and profile photo.
- Users can view and edit only their own profile.
- Duplicate-email protection on updates.

### User Interface
- Responsive public landing page.
- Light and dark themes with a toggle that remembers the choice.
- Accessible forms with inline validation feedback.
- Consistent branding and responsive layouts across public and signed-in pages.
- Lessons path with level sections, completion states, and a next-lesson flow.
- Sandbox workspace with a schema rail, query history, and saved queries.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.1 |
| Frontend | Django Templates, HTML, CSS, JavaScript |
| Application Database | PostgreSQL (Supabase) |
| Practice Engine | Isolated in-memory SQLite |
| Configuration | python-dotenv |
| Image Processing | Pillow |
| Testing | Django Test Framework |
| Runtime | Python 3.12+ |

## Getting Started

### Prerequisites

- Python 3.12 or newer
- PostgreSQL database
- Git

### 1. Clone the repository

```bash
git clone https://github.com/jamuelbacus/SQLPlayground-Bacus-Jamuel-G2.git
cd SQLPlayground-Bacus-Jamuel-G2
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the committed template to a `.env` file in the project root and fill in your own values:

```bash
cp .env.example .env
```

The template contains:

```dotenv
# Copy this file to .env and fill in real values. Never commit .env.

# Django secret key. Generate one with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=replace-with-a-generated-secret-key

# Set to True only for local development. Defaults to False.
DEBUG=False

# Comma-separated hostnames. Defaults to 127.0.0.1,localhost.
ALLOWED_HOSTS=127.0.0.1,localhost

# Comma-separated trusted origins for CSRF. Safe to leave empty locally.
CSRF_TRUSTED_ORIGINS=

# PostgreSQL (Supabase) connection settings.
# DB_NAME and DB_PORT have safe defaults when omitted.
DB_NAME=postgres
DB_USER=replace-with-database-user
DB_PASSWORD=replace-with-database-password
DB_HOST=replace-with-database-host
DB_PORT=5432
```

Replace every `replace-with-*` placeholder before the first run. Generate a Django secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django application secret key |
| `DEBUG` | Enables or disables debug mode |
| `ALLOWED_HOSTS` | Allowed application hostnames |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF protection |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | Database username |
| `DB_PASSWORD` | Database password |
| `DB_HOST` | Database host |
| `DB_PORT` | Database port (default: 5432) |

Startup with the default settings fails fast when `SECRET_KEY`, `DB_USER`, `DB_PASSWORD`, or `DB_HOST` is missing; the error names every missing variable. `.env` stays ignored by Git. The test settings module skips this validation, so the suite runs with `--settings=sqlplayground.settings_test` and no production credentials.

### 5. Apply database migrations

```bash
python manage.py migrate
```

The School Database used by lessons and the sandbox is seeded automatically in an isolated in-memory SQLite connection. It does not create or modify tables in the hosted PostgreSQL database.

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

Superusers are automatically assigned the Administrator role, even when no role is chosen during creation.

### 7. Run the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Routes

| URL | Access | Description |
|---|---|---|
| `/` | Public | Landing page |
| `/signup/` | Public | Learner registration |
| `/login/` | Public | User login |
| `/logout/` | Authenticated | User logout (POST only) |
| `/dashboard/` | Authenticated | Role-based dashboard redirect |
| `/dashboard/learner/` | Learner | Learner dashboard |
| `/lessons/` | Learner | Guided lesson path |
| `/lessons/<slug>/` | Learner | Lesson brief, editor, and result |
| `/lessons/<slug>/check/` | Learner | Run and check a lesson query (POST) |
| `/sandbox/` | Learner | Free SQL sandbox |
| `/sandbox/execute/` | Learner | Run a `SELECT` statement (POST) |
| `/sandbox/saved/` | Learner | Saved query list |
| `/sandbox/saved/new/` | Learner | Save a new query |
| `/sandbox/saved/<id>/` | Learner | Saved query detail |
| `/sandbox/saved/<id>/edit/` | Learner | Edit a saved query |
| `/sandbox/saved/<id>/delete/` | Learner | Delete a saved query |
| `/dashboard/administrator/` | Administrator | Administrator dashboard |
| `/dashboard/administrator/users/` | Administrator | Search and manage accounts |
| `/dashboard/administrator/users/new/` | Administrator | Create an account |
| `/dashboard/administrator/users/<id>/edit/` | Administrator | Edit an account |
| `/dashboard/administrator/users/<id>/password/` | Administrator | Change an account password |
| `/dashboard/administrator/users/<id>/delete/` | Administrator | Delete an account |
| `/dashboard/learning/` | Public | Permanent redirect to `/sandbox/` |
| `/profile/` | Authenticated | View profile |
| `/profile/edit/` | Authenticated | Edit profile |

## Testing

Run the test suite:

```bash
python manage.py test --settings=sqlplayground.settings_test
```

`settings_test` swaps in a local SQLite database so the suite runs without connecting to Supabase. It also skips startup validation, so no production credentials are needed. Running `python manage.py test` with the default settings still requires the same environment variables as any other startup.

The current test suite contains 120 tests covering:

- Registration and input validation
- Password hashing
- Login and logout, including the remember me option
- Protected routes and role-based dashboard access
- Profile ownership and updates
- Public and signed-in page layouts, including the Lessons and Sandbox navigation
- Administrator user management and self-lockout protections
- Saved query ownership and SQL execution restrictions
- Guided lesson curriculum, grading, attempt counts, and completion
- Sandbox isolation from application tables, row limits, timeouts, and history
- Permanent redirect from the old learning route to the sandbox
- Configuration template and fail-fast validation of required environment variables

## Project Structure

```text
.
├── .env.example     # Committed template of supported environment variables
├── accounts/        # Authentication, roles, profiles, and account tests
├── dashboard/       # Role dashboards, sandbox, saved queries, user management
│   └── migrations/  # QueryHistory and SavedQuery schema
├── lessons/         # Guided curriculum, isolated practice engine, progress
│   └── migrations/  # LessonProgress schema
├── sqlplayground/   # Project settings, test settings, and URL configuration
├── static/          # CSS, JavaScript, and brand assets
├── templates/       # HTML templates
├── docs/            # Project documentation
├── manage.py
└── requirements.txt
```

## Roadmap

- [x] User registration and authentication
- [x] Role-based dashboards
- [x] Profile management
- [x] Interactive SQL editor
- [x] SQL query execution
- [x] Sample database
- [x] Query history and saved queries
- [x] Administrator user management without the Django admin site
- [x] Guided lessons with automatic result checking and saved progress
- [x] Isolated free sandbox with schema, history, and saved queries
- [ ] Additional sample databases and lesson tracks
- [ ] Richer query feedback and explanations

## Authors

Created and maintained by the SQL Playground Team.

## License

This project is intended for academic and educational purposes only. All rights reserved by the authors.
