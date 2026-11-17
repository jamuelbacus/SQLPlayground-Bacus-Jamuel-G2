"""Test settings.

Run the suite without the hosted PostgreSQL database:

    python manage.py test --settings=sqlplayground.settings_test

Production settings are unchanged. Django uses an in-memory SQLite database
for the test run.
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",
    }
}
