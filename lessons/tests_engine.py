from unittest.mock import patch

from django.test import SimpleTestCase

from lessons import engine
from lessons.engine import (
    BLANK_SQL_MESSAGE,
    MAX_SQL_LENGTH,
    MULTIPLE_STATEMENTS_MESSAGE,
    NON_SELECT_SQL_MESSAGE,
    TOO_LONG_SQL_MESSAGE,
    READ_ONLY_DENIED_MESSAGE,
    QueryError,
    run_query,
    validate_read_only_sql,
)


class SqlValidationTests(SimpleTestCase):
    def test_exact_length_boundary_is_accepted_before_scan(self):
        sql = "SELECT " + "x" * (MAX_SQL_LENGTH - len("SELECT "))

        with patch("lessons.engine._sql_code", wraps=engine._sql_code) as scanner:
            validate_read_only_sql(sql)

        self.assertEqual(len(sql), MAX_SQL_LENGTH)
        scanner.assert_called_once_with(sql)

    def test_overlength_is_rejected_before_scan(self):
        sql = "SELECT " + "x" * (MAX_SQL_LENGTH - len("SELECT ") + 1)

        with patch("lessons.engine._sql_code", wraps=engine._sql_code) as scanner:
            with self.assertRaisesMessage(QueryError, TOO_LONG_SQL_MESSAGE):
                validate_read_only_sql(sql)

        self.assertEqual(len(sql), MAX_SQL_LENGTH + 1)
        scanner.assert_not_called()

    def test_blank_and_comment_only_sql_are_rejected(self):
        for sql in ("   ", "/* comment */\r-- comment"):
            with self.subTest(sql=sql):
                with self.assertRaisesMessage(QueryError, BLANK_SQL_MESSAGE):
                    validate_read_only_sql(sql)

    def test_non_select_statement_is_rejected(self):
        with self.assertRaisesMessage(QueryError, NON_SELECT_SQL_MESSAGE):
            validate_read_only_sql("DELETE FROM students")

    def test_backtick_identifier_with_semicolon_is_one_statement(self):
        validate_read_only_sql("SELECT `odd;name` FROM students")

    def test_bracket_identifier_with_semicolon_is_one_statement(self):
        validate_read_only_sql("SELECT [odd;name] FROM students")

    def test_doubled_quotes_inside_string_are_one_statement(self):
        validate_read_only_sql("SELECT 'it''s; fine' FROM students")

    def test_nested_block_comments_are_ignored(self):
        validate_read_only_sql("/* outer /* inner ; */ still */ SELECT 1")

    def test_carriage_return_ends_a_line_comment(self):
        validate_read_only_sql("-- note\rSELECT 1")

    def test_carriage_return_multiple_statements_are_rejected(self):
        with self.assertRaisesMessage(QueryError, MULTIPLE_STATEMENTS_MESSAGE):
            validate_read_only_sql("-- note\rSELECT 1; SELECT 2")

    def test_authorizer_denial_uses_friendly_message(self):
        with self.assertRaisesMessage(QueryError, READ_ONLY_DENIED_MESSAGE):
            run_query("WITH c AS (SELECT 1) DELETE FROM students")
