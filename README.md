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

SQL Playground is a web-based learning platform that allows IT students to practice SQL through interactive query writing and execution. Students open a sample School Database, write a query in the editor, run it, and see the results in the browser without installing a database server.

The project now covers the full learner flow: registration, login, role-based dashboards, profile management, a SQL practice workspace, saved queries, and query history. Administrator functions are built into the project at `/dashboard/administrator/`; the Django admin site is not installed. Invalid or disallowed statements return a clear message, and every execution is recorded in the learner's query history.

## Features

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
- Learner dashboard shows saved query count, practice exercises, sample databases, total queries executed, and a progress bar.

### SQL Practice Workspace
- Built-in School Database with `students`, `courses`, and `enrollments` tables, created automatically with sample rows on first use.
- Schema viewer listing each table's columns and sample rows.
- SQL editor that runs one `SELECT` statement at a time; blank input, non-`SELECT` statements, and multiple statements are rejected with a clear message.
- Results table with returned columns, rows, and row count.
- Query history showing the 10 most recent executions for the signed-in learner.
- Saved queries with create, view, edit, and delete, scoped to the owning learner.
- Editor contents and the last result are kept in the session so the workspace survives redirects.

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

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.1 |
| Frontend | Django Templates, HTML, CSS, JavaScript |
| Database | PostgreSQL (Supabase) |
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

Create a `.env` file in the project root:

```dotenv
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=

DB_NAME=postgres
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
DB_PORT=5432
```

Generate a Django secret key:

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

### 5. Apply database migrations

```bash
python manage.py migrate
```

The School Database tables used by the practice workspace are created automatically the first time a learner opens the workspace.

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
| `/dashboard/learning/` | Learner | SQL practice workspace |
| `/dashboard/learning/execute/` | Learner | Run a `SELECT` statement (POST) |
| `/dashboard/learning/saved/` | Learner | Saved query list |
| `/dashboard/learning/saved/new/` | Learner | Save a new query |
| `/dashboard/learning/saved/<id>/` | Learner | Saved query detail |
| `/dashboard/learning/saved/<id>/edit/` | Learner | Edit a saved query |
| `/dashboard/learning/saved/<id>/delete/` | Learner | Delete a saved query |
| `/dashboard/administrator/` | Administrator | Administrator dashboard |
| `/dashboard/administrator/users/` | Administrator | Search and manage accounts |
| `/dashboard/administrator/users/new/` | Administrator | Create an account |
| `/dashboard/administrator/users/<id>/edit/` | Administrator | Edit an account |
| `/dashboard/administrator/users/<id>/password/` | Administrator | Change an account password |
| `/dashboard/administrator/users/<id>/delete/` | Administrator | Delete an account |
| `/profile/` | Authenticated | View profile |
| `/profile/edit/` | Authenticated | Edit profile |

## Testing

Run the test suite:

```bash
python manage.py test
```

The current test suite contains 63 tests covering:

- Registration and input validation
- Password hashing
- Login and logout, including the remember me option
- Protected routes and role-based dashboard access
- Profile ownership and updates
- Public and signed-in page layouts
- Administrator user management and self-lockout protections
- Saved query ownership and SQL execution restrictions

A local PostgreSQL instance may be used for testing if the hosted database does not permit test database creation.

## Project Structure

```text
.
├── accounts/        # Authentication, roles, profiles, and account tests
├── dashboard/       # Role dashboards, SQL workspace, saved queries, user management
│   └── migrations/  # QueryHistory and SavedQuery schema
├── sqlplayground/   # Project settings and URL configuration
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
- [ ] Additional sample databases and guided exercises
- [ ] Richer query feedback and explanations

## Authors

Created and maintained by the SQL Playground Team.

## License

This project is intended for academic and educational purposes only. All rights reserved by the authors.
