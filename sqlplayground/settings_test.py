"""Test settings.

The plain test command selects this module automatically:

    python manage.py test

The explicit compatibility command remains supported:

    python manage.py test --settings=sqlplayground.settings_test

Production settings are unchanged. Django uses an in-memory SQLite database
for the test run.
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
