<p align="center">
  <img src="static/img/project-logo-transparent.svg" alt="SQL Playground logo" width="104" />
</p>

<h1 align="center">SQL Playground</h1>

<p align="center">
  <strong>Practice SQL in the browser.</strong><br />
  A web-based application that helps IT students learn SQL through hands-on
  practice with real databases.
</p>

<p align="center">
  <a href="https://www.djangoproject.com/"><img src="https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white" alt="Django 6.1" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12 or newer" /></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL on Supabase" /></a>
  <img src="https://img.shields.io/badge/project-academic-1F6BFF" alt="Academic project" />
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#features">Features</a> ·
  <a href="#tech-stack">Tech stack</a> ·
  <a href="#getting-started">Getting started</a> ·
  <a href="#routes">Routes</a> ·
  <a href="#testing">Testing</a> ·
  <a href="#authors">Authors</a>
</p>

---

## Overview

SQL Playground is a web-based application for IT students who are learning SQL.
It gives students one place to practice: open a sample database, write a query
in the editor, and run it to see the results. When a query is logically wrong,
the application explains the mistake in plain language and points to the
concept worth reviewing.

Students do not need to install a database server or set up a local
environment. They create an account, sign in, and practice in the browser.
Learner and administrator roles keep the experience focused, and the profile
page lets students keep their account details up to date.

The application includes sample databases, query feedback, accounts, a SQL
editor, a schema viewer, and query history. The goal is to make learning SQL
easier and less frustrating by connecting every query to a clear result and a
useful explanation.

## Features

### Practice workspace

- Run SQL queries against sample databases and see the results in the browser.
- Get plain-language feedback when a query is logically wrong, including a hint
  about the concept to review.
- Browse tables, columns, and relationships in the schema viewer before writing
  a query.
- Review earlier work in the query history and rerun a saved query.

### Accounts and access

- Learner registration with required-field, email-format, unique username,
  unique email, and password-confirmation validation.
- Passwords hashed by Django's authentication system, with Django's standard
  password validators enabled.
- Login with a username or an email address, and a single, clear
  invalid-credentials message.
- Remember me option for sessions that should survive a browser restart.
- POST-only logout protected by CSRF.
- Protected routes that redirect anonymous visitors to the login page.

### Role-based experience

- Separate dashboards for **Learner** and **Administrator** accounts.
- Server-side role checks, so a learner cannot reach the administrator
  dashboard by typing its URL, and vice versa.
- Self-registration always creates a Learner. Administrator access is granted
  only through `createsuperuser` or the Django admin site.

### Profiles

- Personal profile view and self-service editing for name, email, contact
  number, and profile photo.
- Users can view and edit only their own profile.
- Contact-number validation and duplicate-email protection on updates.
- Uploaded photos are served from the media directory during development.

### Experience and design

- Public landing page that explains the product and its learning goals.
- Responsive, server-rendered templates with accessible forms and clear
  validation feedback.
- Light and dark themes with a visible toggle that remembers the choice.
- Consistent brand assets, including a transparent logo and favicon set.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Django 6.1 |
| Frontend | Django templates, HTML, CSS |
| Database | PostgreSQL, hosted on Supabase |
| Configuration | `python-dotenv` with a local `.env` file |
| Media | Pillow for profile photo uploads |
| Testing | Django test runner |
| Runtime | Python 3.12 or newer |

## Roles

| Role | How it is created | Dashboard |
| --- | --- | --- |
| Learner | Self-registration at `/signup/` | `/dashboard/learner/` |
| Administrator | `createsuperuser` or the Django admin | `/dashboard/administrator/` |

The role field is never exposed on the public registration form. Every new
signup is a Learner, and superusers are promoted to Administrator automatically.

## Getting started

### Prerequisites

- Python 3.12 or newer
- A PostgreSQL database, such as a Supabase project
- `git`

### 1. Clone the repository

```bash
git clone https://github.com/jamuelbacus/SQLPlayground-Bacus-Jamuel-G2.git
cd SQLPlayground-Bacus-Jamuel-G2
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the environment

Create a `.env` file in the project root with the following keys:

```dotenv
SECRET_KEY=replace-with-a-strong-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=

DB_NAME=postgres
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
DB_PORT=5432
```

Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

| Variable | Required | Notes |
| --- | --- | --- |
| `SECRET_KEY` | Yes | Django signing key. Never commit it. |
| `DEBUG` | No | Defaults to `False`. Set `True` for local development. |
| `ALLOWED_HOSTS` | No | Comma-separated. Defaults to `127.0.0.1,localhost`. |
| `CSRF_TRUSTED_ORIGINS` | No | Comma-separated origins for proxied deployments. |
| `DB_NAME` | No | Defaults to `postgres`. |
| `DB_USER` | Yes | PostgreSQL user. |
| `DB_PASSWORD` | Yes | PostgreSQL password. |
| `DB_HOST` | Yes | PostgreSQL host. |
| `DB_PORT` | No | Defaults to `5432`. |

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create an administrator

```bash
python manage.py createsuperuser
```

The custom user model assigns the Administrator role to superusers
automatically.

### 7. Start the development server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

## Routes

| URL | Access | Purpose |
| --- | --- | --- |
| `/` | Public | Landing page |
| `/signup/` | Public | Learner registration |
| `/login/` | Public | Sign in |
| `/logout/` | Signed in | Sign out (POST only) |
| `/profile/` | Signed in | View own profile |
| `/profile/edit/` | Signed in | Edit own profile |
| `/dashboard/` | Signed in | Redirect to the current role's dashboard |
| `/dashboard/learner/` | Learner | Learner dashboard |
| `/dashboard/administrator/` | Administrator | Administrator dashboard |
| `/admin/` | Staff | Django admin |

## Testing

Run the full suite with:

```bash
python manage.py test
```

The suite covers registration validation, password hashing, login and logout,
username-or-email login, protected routes, role-based dashboard access, profile
ownership, and the public and signed-in interface.

> If your hosted database role cannot create a test database, point the
> `DB_*` variables at a local PostgreSQL instance for the test run. The project
> targets PostgreSQL, not SQLite.

## Project structure

```text
.
├── accounts/        # Custom user, registration, authentication, profiles
├── dashboard/       # Role-based dashboards and routing
├── sqlplayground/   # Project settings and URL configuration
├── static/          # Stylesheet and brand assets
├── templates/       # Shared and feature templates
├── manage.py
└── requirements.txt
```

## Security

- `.env`, virtual environments, caches, uploaded media, and collected static
  files are excluded from version control.
- Database credentials and the Django secret key are never committed.
- Logout is a POST request protected by CSRF.
- Role checks run on the server, not only in navigation.
- Passwords are stored as Django password hashes.
- Registration and profile forms validate input on the server.
- For production, set `DEBUG=False`, use a strong `SECRET_KEY`, and serve
  static and media files through your web server.

## Authors

SQL Playground is an academic project built by the project team for an IT
course at Cebu Institute of Technology - University. It is not a capstone
project.

## License

This repository is published for academic review and portfolio use. No
open-source license is currently included. Contact the maintainers before
redistributing or reusing the code.
