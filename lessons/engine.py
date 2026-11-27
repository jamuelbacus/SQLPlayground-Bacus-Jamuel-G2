"""Isolated SQL practice engine.

Learner SQL runs against a fresh in-memory SQLite database seeded with the
School Database. Application tables are never reachable from this engine, and
queries are limited to read-only statements.
"""

from __future__ import annotations

import sqlite3
import time
from typing import NamedTuple

MAX_ROWS = 200
MAX_SECONDS = 1.0
MAX_STEPS = 1_000_000
MAX_SQL_LENGTH = 5000

BLANK_SQL_MESSAGE = "Please enter a SQL statement."
TOO_LONG_SQL_MESSAGE = "SQL query is too long."
NON_SELECT_SQL_MESSAGE = "Only SELECT queries are allowed in the SQL playground."
MULTIPLE_STATEMENTS_MESSAGE = "Run one SQL statement at a time."
READ_ONLY_DENIED_MESSAGE = "This query is not allowed. Use a read-only SQL statement."

TABLE_NAMES = ("students", "courses", "enrollments")

STUDENTS = (
    (1, "Alice", "Smith", "alice@example.com", 2024),
    (2, "Bob", "Jones", "bob@example.com", 2023),
    (3, "Charlie", "Brown", "charlie@example.com", 2024),
    (4, "Diana", "Miller", "diana@example.com", 2022),
    (5, "Ethan", "Davis", "ethan@example.com", 2024),
    (6, "Fiona", "Clark", "fiona@example.com", 2023),
)

COURSES = (
    (1, "Database Fundamentals", 3),
    (2, "Web Development", 3),
    (3, "Statistics", 2),
    (4, "Data Structures", 4),
    (5, "Operating Systems", 3),
)

ENROLLMENTS = (
    (1, 1, 1, "A"),
    (2, 1, 2, "B"),
    (3, 2, 1, "A"),
    (4, 2, 3, "B"),
    (5, 3, 2, "A"),
    (6, 3, 4, "B"),
    (7, 4, 1, "B"),
    (8, 5, 4, "A"),
)


class QueryError(Exception):
    """Raised when a learner query cannot be executed."""


class QueryTimeout(QueryError):
    """Raised when a query exceeds the practice engine limits."""


class QueryResult(NamedTuple):
    columns: list[str]
    rows: list[tuple]
    truncated: bool = False


def _build_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            enrollment_year INTEGER NOT NULL
        );
        CREATE TABLE courses (
            course_id INTEGER PRIMARY KEY,
            course_name TEXT NOT NULL,
            credits INTEGER NOT NULL
        );
        CREATE TABLE enrollments (
            enrollment_id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(student_id),
            course_id INTEGER NOT NULL REFERENCES courses(course_id),
            grade TEXT NOT NULL
        );
        """
    )
    connection.executemany(
        "INSERT INTO students VALUES (?, ?, ?, ?, ?)", STUDENTS
    )
    connection.executemany(
        "INSERT INTO courses VALUES (?, ?, ?)", COURSES
    )
    connection.executemany(
        "INSERT INTO enrollments VALUES (?, ?, ?, ?)", ENROLLMENTS
    )
    connection.commit()
    return connection


def schema_tables() -> list[dict]:
    """Return the practice tables, their columns, and a few sample rows."""
    connection = _build_connection()
    try:
        tables = []
        for table_name in TABLE_NAMES:
            info = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
            columns = [row[1] for row in info]
            rows = connection.execute(
                f'SELECT * FROM "{table_name}" LIMIT 5'
            ).fetchall()
            tables.append(
                {"name": table_name, "columns": columns, "rows": rows}
            )
        return tables
    finally:
        connection.close()


_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
}
if hasattr(sqlite3, "SQLITE_RECURSIVE"):
    _ALLOWED_ACTIONS.add(sqlite3.SQLITE_RECURSIVE)


def _authorizer(action, arg1, arg2, dbname, trigger):
    return sqlite3.SQLITE_OK if action in _ALLOWED_ACTIONS else sqlite3.SQLITE_DENY


def _sql_code(sql: str) -> str:
    """Blank comments while preserving literals, identifiers, and positions."""
    output = []
    index = 0
    block_depth = 0
    quote = None
    while index < len(sql):
        char = sql[index]
        following = sql[index + 1] if index + 1 < len(sql) else ""

        if quote is not None:
            closing = "]" if quote == "[" else quote
            output.append(char)
            if char == closing:
                if following == closing:
                    output.append(following)
                    index += 2
                    continue
                quote = None
            index += 1
            continue

        if block_depth:
            if char == "/" and following == "*":
                block_depth += 1
                output.extend("  ")
                index += 2
                continue
            if char == "*" and following == "/":
                block_depth -= 1
                output.extend("  ")
                index += 2
                continue
            output.append("\n" if char in "\r\n" else " ")
            index += 1
            continue

        if char == "-" and following == "-":
            output.extend("  ")
            index += 2
            while index < len(sql) and sql[index] not in "\r\n":
                output.append(" ")
                index += 1
            continue
        if char == "/" and following == "*":
            block_depth = 1
            output.extend("  ")
            index += 2
            continue
        if char in ("'", '"', "`", "["):
            quote = char
        output.append(char)
        index += 1
    return "".join(output)


def _skip_quoted(code: str, index: int, quote: str) -> int:
    closing = "]" if quote == "[" else quote
    index += 1
    while index < len(code):
        if code[index] == closing:
            if index + 1 < len(code) and code[index + 1] == closing:
                index += 2
                continue
            return index + 1
        index += 1
    return index


def _has_multiple_statements(sql: str, code: str) -> bool:
    index = 0
    while index < len(code):
        char = code[index]
        if char in ("'", '"', "`", "["):
            index = _skip_quoted(code, index, char)
            continue
        if char == ";" and sqlite3.complete_statement(
            sql[: index + 1].replace("\r", "\n")
        ):
            if code[index + 1 :].strip():
                return True
        index += 1
    return False


def _first_keyword(code: str) -> str:
    text = code.strip()
    if not text:
        return ""
    return text.split(None, 1)[0].lower()


def validate_read_only_sql(sql: str) -> None:
    """Check that learner SQL is one bounded, read-only statement."""
    text = (sql or "").strip()
    if not text:
        raise QueryError(BLANK_SQL_MESSAGE)
    if len(text) > MAX_SQL_LENGTH:
        raise QueryError(TOO_LONG_SQL_MESSAGE)

    code = _sql_code(text)
    if not code.strip():
        raise QueryError(BLANK_SQL_MESSAGE)
    if _first_keyword(code) not in {"select", "with"}:
        raise QueryError(NON_SELECT_SQL_MESSAGE)
    if _has_multiple_statements(text, code):
        raise QueryError(MULTIPLE_STATEMENTS_MESSAGE)


def run_query(sql: str) -> QueryResult:
    """Run one read-only practice query and return its result."""
    text = (sql or "").strip()
    validate_read_only_sql(text)

    connection = _build_connection()
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.set_authorizer(_authorizer)
        started = time.monotonic()
        steps = 0
        timed_out = False

        def guard():
            nonlocal steps, timed_out
            steps += 1
            if time.monotonic() - started > MAX_SECONDS or steps > MAX_STEPS:
                timed_out = True
                return 1
            return 0

        connection.set_progress_handler(guard, 1000)

        try:
            cursor = connection.execute(text)
            columns = [item[0] for item in (cursor.description or [])]
            rows = cursor.fetchmany(MAX_ROWS + 1)
        except sqlite3.OperationalError as exc:
            if timed_out:
                raise QueryTimeout(
                    "This query took too long. Try a simpler query."
                ) from exc
            raise QueryError(f"SQL error: {exc}") from exc
        except (sqlite3.ProgrammingError, sqlite3.Warning) as exc:
            raise QueryError("Run one SQL statement at a time.") from exc
        except sqlite3.DatabaseError as exc:
            if "not authorized" in str(exc).lower():
                raise QueryError(READ_ONLY_DENIED_MESSAGE) from exc
            raise QueryError(f"SQL error: {exc}") from exc
        except sqlite3.Error as exc:
            raise QueryError(f"SQL error: {exc}") from exc
    finally:
        connection.close()

    truncated = len(rows) > MAX_ROWS
    if truncated:
        rows = rows[:MAX_ROWS]
    return QueryResult(columns, [tuple(row) for row in rows], truncated)


def _normalize_cell(value):
    if value is None:
        return ("none", 0.0)
    if isinstance(value, bool):
        return ("num", float(value))
    if isinstance(value, (int, float)):
        return ("num", round(float(value), 6))
    return ("str", str(value))


def results_match(
    actual: QueryResult, expected: QueryResult, ordered: bool
) -> bool:
    """Compare learner results with the lesson reference result."""
    if len(actual.columns) != len(expected.columns):
        return False
    if len(actual.rows) != len(expected.rows):
        return False

    actual_rows = [
        tuple(_normalize_cell(value) for value in row) for row in actual.rows
    ]
    expected_rows = [
        tuple(_normalize_cell(value) for value in row) for row in expected.rows
    ]
    if ordered:
        return actual_rows == expected_rows
    return sorted(actual_rows) == sorted(expected_rows)
