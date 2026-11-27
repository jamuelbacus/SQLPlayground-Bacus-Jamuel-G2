import sqlite3
from unittest.mock import patch

from django.test import SimpleTestCase

from lessons import engine
from lessons.engine import (
    BLANK_SQL_MESSAGE,
    MAX_ROWS,
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


STABLE_REJECTION = "Only SELECT queries are allowed in the SQL playground."
AUTHORIZER_REJECTION = READ_ONLY_DENIED_MESSAGE
CTE_DROP_REJECTION = 'SQL error: near "DROP": syntax error'
SEED_COUNTS = {"students": 6, "courses": 5, "enrollments": 8}

INSERT_SQL = "INSERT INTO students VALUES (99, 'Mallory', 'X', 'm@example.com', 2026)"
UPDATE_SQL = "UPDATE students SET first_name = 'Hacked' WHERE student_id = 1"
DELETE_SQL = "DELETE FROM students WHERE student_id = 1"
DROP_SQL = "DROP TABLE students"
ALTER_SQL = "ALTER TABLE students ADD COLUMN hacked TEXT"
CREATE_SQL = "CREATE TABLE hacked (id INTEGER)"
REPLACE_SQL = "REPLACE INTO students VALUES (99, 'Mallory', 'X', 'm@example.com', 2026)"
PRAGMA_SQL = "PRAGMA table_info(students)"
ATTACH_SQL = "ATTACH DATABASE ':memory:' AS other"
DETACH_SQL = "DETACH DATABASE other"
VACUUM_SQL = "VACUUM"
REINDEX_SQL = "REINDEX"
TRIGGER_SQL = "CREATE TRIGGER bad AFTER INSERT ON students BEGIN SELECT 1; END"

CTE_INSERT_SQL = (
    "WITH c AS (SELECT 1) "
    "INSERT INTO students VALUES (99, 'Mallory', 'X', 'm@example.com', 2026)"
)
CTE_UPDATE_SQL = (
    "WITH c AS (SELECT 1) "
    "UPDATE students SET first_name = 'Hacked' WHERE student_id = 1"
)
CTE_DELETE_SQL = "WITH c AS (SELECT 1) DELETE FROM students WHERE student_id = 1"
CTE_DROP_SQL = "WITH c AS (SELECT 1) DROP TABLE students"

DIRECT_WRITE_STATEMENTS = (
    INSERT_SQL,
    UPDATE_SQL,
    DELETE_SQL,
    DROP_SQL,
    ALTER_SQL,
    CREATE_SQL,
    REPLACE_SQL,
    PRAGMA_SQL,
    ATTACH_SQL,
    DETACH_SQL,
    VACUUM_SQL,
    REINDEX_SQL,
    TRIGGER_SQL,
)
CTE_WRITE_STATEMENTS = (CTE_INSERT_SQL, CTE_UPDATE_SQL, CTE_DELETE_SQL)


class SnapshotConnection(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.snapshot = None

    def close(self):
        try:
            self.snapshot = {
                name: self.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in SEED_COUNTS
            }
        except sqlite3.Error as exc:
            self.snapshot = {"error": str(exc)}
        super().close()


def assert_rejected_without_mutation(test_case, sql, expected_message):
    connections = []

    def connect(*args, **kwargs):
        connection = SnapshotConnection(*args, **kwargs)
        connections.append(connection)
        return connection

    with patch.object(engine.sqlite3, "connect", side_effect=connect):
        connection = engine._build_connection()
        with patch.object(engine, "_build_connection", return_value=connection):
            with test_case.assertRaises(QueryError) as raised:
                engine.run_query(sql)
        # Leading-verb rejection happens before run_query closes its connection.
        if connection.snapshot is None:
            connection.close()

    test_case.assertEqual(str(raised.exception), expected_message)
    test_case.assertEqual(connections[0].snapshot, SEED_COUNTS)


class SqlWriteRejectionTests(SimpleTestCase):
    def test_insert_is_rejected(self):
        assert_rejected_without_mutation(self, INSERT_SQL, STABLE_REJECTION)

    def test_update_is_rejected(self):
        assert_rejected_without_mutation(self, UPDATE_SQL, STABLE_REJECTION)

    def test_delete_is_rejected(self):
        assert_rejected_without_mutation(self, DELETE_SQL, STABLE_REJECTION)

    def test_drop_is_rejected(self):
        assert_rejected_without_mutation(self, DROP_SQL, STABLE_REJECTION)

    def test_alter_is_rejected(self):
        assert_rejected_without_mutation(self, ALTER_SQL, STABLE_REJECTION)

    def test_create_is_rejected(self):
        assert_rejected_without_mutation(self, CREATE_SQL, STABLE_REJECTION)

    def test_replace_is_rejected(self):
        assert_rejected_without_mutation(self, REPLACE_SQL, STABLE_REJECTION)

    def test_pragma_is_rejected(self):
        assert_rejected_without_mutation(self, PRAGMA_SQL, STABLE_REJECTION)

    def test_attach_is_rejected(self):
        assert_rejected_without_mutation(self, ATTACH_SQL, STABLE_REJECTION)

    def test_detach_is_rejected(self):
        assert_rejected_without_mutation(self, DETACH_SQL, STABLE_REJECTION)

    def test_vacuum_is_rejected(self):
        assert_rejected_without_mutation(self, VACUUM_SQL, STABLE_REJECTION)

    def test_reindex_is_rejected(self):
        assert_rejected_without_mutation(self, REINDEX_SQL, STABLE_REJECTION)

    def test_trigger_creation_is_rejected(self):
        assert_rejected_without_mutation(self, TRIGGER_SQL, STABLE_REJECTION)

    def test_cte_wrapped_insert_is_rejected(self):
        assert_rejected_without_mutation(
            self, CTE_INSERT_SQL, AUTHORIZER_REJECTION
        )

    def test_cte_wrapped_update_is_rejected(self):
        assert_rejected_without_mutation(
            self, CTE_UPDATE_SQL, AUTHORIZER_REJECTION
        )

    def test_cte_wrapped_delete_is_rejected(self):
        assert_rejected_without_mutation(
            self, CTE_DELETE_SQL, AUTHORIZER_REJECTION
        )

    def test_cte_wrapped_drop_is_rejected(self):
        assert_rejected_without_mutation(
            self, CTE_DROP_SQL, CTE_DROP_REJECTION
        )

    def test_select_still_runs(self):
        result = run_query("SELECT first_name FROM students WHERE student_id = 1")

        self.assertEqual(result.rows, [("Alice",)])

    def test_with_still_runs(self):
        result = run_query(
            "WITH names AS (SELECT first_name FROM students) "
            "SELECT first_name FROM names WHERE first_name = 'Bob'"
        )

        self.assertEqual(result.rows, [("Bob",)])

    def test_recursive_cte_still_runs(self):
        result = run_query(
            "WITH RECURSIVE nums(n) AS ("
            "SELECT 1 UNION ALL SELECT n + 1 FROM nums WHERE n < 250"
            ") SELECT n FROM nums"
        )

        self.assertEqual(len(result.rows), MAX_ROWS)
