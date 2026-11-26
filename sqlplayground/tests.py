import os
import sys
from unittest import mock

from django.test import SimpleTestCase

import manage
import sqlplayground.settings as production_settings
import sqlplayground.settings_test as isolated_settings


class ManageCommandSettingsTests(SimpleTestCase):
    def run_main_and_capture_settings(self, argv, environ):
        with mock.patch.object(sys, "argv", argv), mock.patch.dict(
            os.environ, environ, clear=True
        ), mock.patch("django.core.management.execute_from_command_line"):
            manage.main()
            return os.environ.get("DJANGO_SETTINGS_MODULE")

    def test_test_command_defaults_to_sqlite_settings(self):
        actual = self.run_main_and_capture_settings(
            ["manage.py", "test"], {}
        )

        self.assertEqual(actual, "sqlplayground.settings_test")

    def test_non_test_command_keeps_production_settings(self):
        actual = self.run_main_and_capture_settings(
            ["manage.py", "check"], {}
        )

        self.assertEqual(actual, "sqlplayground.settings")

    def test_explicit_settings_option_is_not_overridden(self):
        actual = self.run_main_and_capture_settings(
            ["manage.py", "test", "--settings=custom.settings"], {}
        )

        self.assertIsNone(actual)

    def test_existing_settings_environment_is_respected(self):
        actual = self.run_main_and_capture_settings(
            ["manage.py", "test"],
            {"DJANGO_SETTINGS_MODULE": "custom.settings"},
        )

        self.assertEqual(actual, "custom.settings")


class TestSettingsDatabaseTests(SimpleTestCase):
    def test_test_settings_use_in_memory_sqlite(self):
        database = isolated_settings.DATABASES["default"]

        self.assertEqual(database["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(database["NAME"], ":memory:")

    def test_production_settings_keep_postgresql(self):
        database = production_settings.DATABASES["default"]

        self.assertEqual(
            database["ENGINE"], "django.db.backends.postgresql"
        )
