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

SQL Playground is a web-based learning platform that allows IT students to practice SQL through interactive query writing and execution. It aims to make learning databases more accessible through sample datasets, instant query results, and explanations of common SQL mistakes.

The current development phase focuses on authentication, role-based dashboards, and profile management. SQL editing and execution features are planned for subsequent development.

## Features

### User Accounts
- Learner registration with input validation.
- Login using username or email.
- Secure password hashing and validation.
- Session-based authentication and protected routes.
- CSRF-protected logout.

### Role-Based Dashboards
- Separate dashboards for Learners and Administrators.
- Server-side role-based access control.
- Automatic Learner assignment during public registration.
- Administrator accounts managed through Django's administrative tools.

### Profile Management
- View and edit personal profile information.
- Update name and email address.
- Upload and update profile photos.
- Profile ownership and input validation.

### User Interface
- Responsive public landing page.
- Consistent branding and visual design.
- Accessible forms with validation feedback.
- Light and dark theme support.

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

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

Superusers are automatically assigned the Administrator role.

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
| `/logout/` | Authenticated | User logout |
| `/dashboard/` | Authenticated | Role-based dashboard redirect |
| `/dashboard/learner/` | Learner | Learner dashboard |
| `/dashboard/administrator/` | Administrator | Administrator dashboard |
| `/profile/` | Authenticated | View profile |
| `/profile/edit/` | Authenticated | Edit profile |
| `/admin/` | Staff | Django administration |

## Testing

Run the test suite:

```bash
python manage.py test
```

The current test suite contains 28 tests covering:

- Registration and input validation
- Password hashing
- Login and logout
- Protected routes
- Role-based dashboard access
- Profile ownership and updates

A local PostgreSQL instance may be used for testing if the hosted database does not permit test database creation.

## Project Structure

```text
.
├── accounts/        # User authentication and profiles
├── dashboard/       # Role-based dashboards
├── sqlplayground/   # Project settings and URL configuration
├── static/          # CSS and brand assets
├── templates/       # HTML templates
├── manage.py
└── requirements.txt
```

## Roadmap

- [x] User registration and authentication
- [x] Role-based dashboards
- [x] Profile management
- [ ] Interactive SQL editor
- [ ] SQL query execution
- [ ] Sample databases and guided exercises
- [ ] Query history and feedback

## Authors

Created and maintained by the SQL Playground Team.

## License

This project is intended for academic and educational purposes only. All rights reserved by the authors.