"""Isolated SQL practice engine.

Learner SQL runs against a fresh in-memory SQLite database seeded with the
School Database. Application tables are never reachable from this engine, and
queries are limited to read-only statements.
"""

from __future__ import annotations

import re
import sqlite3
import time
from typing import NamedTuple

MAX_ROWS = 200
MAX_SECONDS = 1.0
MAX_STEPS = 1_000_000

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

_ALLOWED_FUNCTIONS = frozenset(
    {
        "abs",
        "avg",
        "coalesce",
        "count",
        "glob",
        "group_concat",
        "ifnull",
        "instr",
        "length",
        "like",
        "lower",
        "ltrim",
        "max",
        "min",
        "nullif",
        "printf",
        "replace",
        "round",
        "rtrim",
        "substr",
        "sum",
        "total",
        "trim",
        "typeof",
        "upper",
    }
)

_DENIED_ACTIONS = frozenset(
    {
        sqlite3.SQLITE_ATTACH,
        sqlite3.SQLITE_DETACH,
    }
)


def _authorizer(action, arg1, arg2, dbname, trigger):
    if action in _DENIED_ACTIONS:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        name = (arg2 or "").lower()
        return (
            sqlite3.SQLITE_OK
            if name in _ALLOWED_FUNCTIONS
            else sqlite3.SQLITE_DENY
        )
    return sqlite3.SQLITE_OK if action in _ALLOWED_ACTIONS else sqlite3.SQLITE_DENY


_LEADING_COMMENTS = re.compile(
    r"\A(?:\s*(?:--[^\n]*(?:\n|$)|/\*.*?\*/))*", re.DOTALL
)


def _first_keyword(sql: str) -> str:
    cleaned = _LEADING_COMMENTS.sub("", sql).strip()
    if not cleaned:
        return ""
    return cleaned.split(None, 1)[0].lower()


def run_query(sql: str) -> QueryResult:
    """Run one read-only practice query and return its result."""
    text = (sql or "").strip()
    if not text:
        raise QueryError("Please enter a SQL statement.")
    if _first_keyword(text) not in {"select", "with"}:
        raise QueryError("Only SELECT queries are allowed in the SQL playground.")

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

        # The progress handler runs between SQLite VM steps, so it cannot stop
        # work performed inside a single C-level function call. The authorizer's
        # function allowlist is what keeps expensive helpers (readfile,
        # writefile, randomblob, zeroblob, and future additions) unreachable.
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
