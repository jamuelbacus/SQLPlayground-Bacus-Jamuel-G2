import os
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

import sqlplayground.settings as project_settings


class ConfigurationValidationTests(SimpleTestCase):
    def test_missing_secret_key_is_reported(self):
        required = project_settings.REQUIRED_ENV_VARS
        values = {name: "value" for name in required if name != "SECRET_KEY"}

        with patch.dict(os.environ, values, clear=True):
            with self.assertRaises(ImproperlyConfigured) as caught:
                project_settings.validate_required_config()

        self.assertIn("SECRET_KEY", str(caught.exception))
        self.assertIn(".env.example", str(caught.exception))

    def test_missing_database_values_are_reported_together(self):
        with patch.dict(os.environ, {"SECRET_KEY": "test-secret"}, clear=True):
            with self.assertRaises(ImproperlyConfigured) as caught:
                project_settings.validate_required_config()

        message = str(caught.exception)
        for name in ("DB_USER", "DB_PASSWORD", "DB_HOST"):
            self.assertIn(name, message)

    def test_valid_configuration_passes(self):
        values = {name: "value" for name in project_settings.REQUIRED_ENV_VARS}

        with patch.dict(os.environ, values, clear=True):
            project_settings.validate_required_config()

    def test_validation_mode_depends_on_settings_module(self):
        with patch.dict(
            os.environ, {"DJANGO_SETTINGS_MODULE": "sqlplayground.settings_test"}
        ):
            self.assertTrue(project_settings.uses_test_settings())

        with patch.dict(
            os.environ, {"DJANGO_SETTINGS_MODULE": "sqlplayground.settings"}
        ):
            self.assertFalse(project_settings.uses_test_settings())

    def test_env_example_lists_all_supported_variables_without_secrets(self):
        example = (project_settings.BASE_DIR / ".env.example").read_text()

        for name in (
            "SECRET_KEY",
            "DEBUG",
            "ALLOWED_HOSTS",
            "CSRF_TRUSTED_ORIGINS",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "DB_HOST",
            "DB_PORT",
        ):
            self.assertIn(f"{name}=", example)
        self.assertIn("SECRET_KEY=replace-with-a-generated-secret-key", example)
        self.assertIn("DB_PASSWORD=replace-with-database-password", example)

    def test_gitignore_keeps_env_untracked(self):
        ignored = [
            line.strip() for line in (project_settings.BASE_DIR / ".gitignore").read_text().splitlines()
        ]

        self.assertIn(".env", ignored)
