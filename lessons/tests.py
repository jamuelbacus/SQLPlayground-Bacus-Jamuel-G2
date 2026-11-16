from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase

from .curriculum import LESSONS, LESSONS_BY_SLUG, lessons_for_level, next_lesson
from .engine import (
    MAX_ROWS,
    QueryError,
    QueryResult,
    results_match,
    run_query,
    schema_tables,
)
from .models import LessonProgress

User = get_user_model()


class SeedSchemaTests(SimpleTestCase):
    def test_schema_lists_three_tables_with_columns_and_rows(self):
        tables = schema_tables()

        self.assertEqual(
            [table["name"] for table in tables],
            ["students", "courses", "enrollments"],
        )
        student_table = tables[0]
        self.assertIn("student_id", student_table["columns"])
        self.assertIn("enrollment_year", student_table["columns"])
        self.assertEqual(len(student_table["rows"]), 5)

    def test_seed_keeps_edge_cases_for_joins(self):
        tables = {table["name"]: table for table in schema_tables()}

        student_rows = run_query("SELECT student_id FROM students")
        enrollment_rows = run_query("SELECT DISTINCT student_id FROM enrollments")
        enrolled_ids = {row[0] for row in enrollment_rows.rows}
        student_ids = {row[0] for row in student_rows.rows}

        self.assertTrue(student_ids - enrolled_ids)

        course_rows = run_query("SELECT course_id FROM courses")
        enrolled_course_rows = run_query(
            "SELECT DISTINCT course_id FROM enrollments"
        )
        self.assertTrue(
            {row[0] for row in course_rows.rows}
            - {row[0] for row in enrolled_course_rows.rows}
        )


class RunQueryTests(SimpleTestCase):
    def test_select_returns_columns_and_rows(self):
        result = run_query(
            "SELECT first_name, last_name FROM students WHERE student_id = 1"
        )

        self.assertEqual(result.columns, ["first_name", "last_name"])
        self.assertEqual(result.rows, [("Alice", "Smith")])
        self.assertFalse(result.truncated)

    def test_with_clause_is_allowed(self):
        result = run_query(
            "WITH names AS (SELECT first_name FROM students) "
            "SELECT first_name FROM names WHERE first_name = 'Bob'"
        )

        self.assertEqual(result.rows, [("Bob",)])

    def test_blank_input_is_rejected(self):
        with self.assertRaisesMessage(QueryError, "Please enter a SQL statement"):
            run_query("   ")

    def test_non_select_statement_is_rejected(self):
        with self.assertRaisesMessage(QueryError, "Only SELECT queries"):
            run_query("DELETE FROM students")

    def test_multiple_statements_are_rejected(self):
        with self.assertRaisesMessage(QueryError, "one SQL statement"):
            run_query("SELECT 1; SELECT 2;")

    def test_write_through_cte_is_denied(self):
        with self.assertRaises(QueryError):
            run_query(
                "WITH chosen AS (SELECT 1) DELETE FROM students WHERE student_id = 1"
            )

    def test_application_tables_are_not_reachable(self):
        with self.assertRaises(QueryError):
            run_query("SELECT * FROM accounts_customuser")

    def test_results_are_capped(self):
        result = run_query(
            "WITH RECURSIVE nums(n) AS ("
            "SELECT 1 UNION ALL SELECT n + 1 FROM nums WHERE n < 250"
            ") SELECT n FROM nums"
        )

        self.assertEqual(len(result.rows), MAX_ROWS)
        self.assertTrue(result.truncated)

    @patch("lessons.engine.MAX_SECONDS", 0.01)
    def test_slow_query_times_out(self):
        with self.assertRaisesMessage(QueryError, "took too long"):
            run_query(
                "WITH RECURSIVE nums(n) AS ("
                "SELECT 1 UNION ALL SELECT n + 1 FROM nums"
                ") SELECT COUNT(*) FROM nums"
            )

    def test_database_error_is_reported(self):
        with self.assertRaisesMessage(QueryError, "SQL error"):
            run_query("SELECT missing_column FROM students")


class ResultsMatchTests(SimpleTestCase):
    def test_ordered_results_must_match_sequence(self):
        actual = QueryResult(["n"], [(2,), (1,)])
        expected = QueryResult(["n"], [(1,), (2,)])

        self.assertFalse(results_match(actual, expected, ordered=True))

    def test_unordered_results_ignore_sequence(self):
        actual = QueryResult(["n"], [(2,), (1,)])
        expected = QueryResult(["n"], [(1,), (2,)])

        self.assertTrue(results_match(actual, expected, ordered=False))

    def test_column_alias_is_ignored(self):
        actual = QueryResult(["total"], [(3,)])
        expected = QueryResult(["count"], [(3,)])

        self.assertTrue(results_match(actual, expected, ordered=True))

    def test_column_count_must_match(self):
        actual = QueryResult(["a", "b"], [(1, 2)])
        expected = QueryResult(["a"], [(1,)])

        self.assertFalse(results_match(actual, expected, ordered=True))

    def test_numbers_compare_with_tolerance(self):
        actual = QueryResult(["average"], [(2.5000001,)])
        expected = QueryResult(["average"], [(2.5,)])

        self.assertTrue(results_match(actual, expected, ordered=True))

    def test_row_count_must_match(self):
        actual = QueryResult(["n"], [(1,)])
        expected = QueryResult(["n"], [(1,), (2,)])

        self.assertFalse(results_match(actual, expected, ordered=True))


class CurriculumTests(SimpleTestCase):
    def test_curriculum_has_eight_lessons_in_order(self):
        self.assertEqual(len(LESSONS), 8)
        self.assertEqual(
            [lesson.order for lesson in LESSONS], list(range(1, 9))
        )
        self.assertEqual(len({lesson.slug for lesson in LESSONS}), 8)
        self.assertEqual(set(LESSONS_BY_SLUG), {lesson.slug for lesson in LESSONS})

    def test_levels_are_grouped_in_teaching_order(self):
        beginner = lessons_for_level("Beginner")
        intermediate = lessons_for_level("Intermediate")
        advanced = lessons_for_level("Advanced")

        self.assertEqual(len(beginner), 3)
        self.assertEqual(len(intermediate), 3)
        self.assertEqual(len(advanced), 2)
        self.assertEqual(
            [lesson.order for lesson in beginner + intermediate + advanced],
            list(range(1, 9)),
        )

    def test_every_reference_query_runs_and_returns_rows(self):
        for lesson in LESSONS:
            with self.subTest(lesson=lesson.slug):
                result = run_query(lesson.reference_sql)
                self.assertTrue(result.columns)
                self.assertTrue(result.rows)

    def test_next_lesson_follows_curriculum_order(self):
        self.assertEqual(next_lesson(LESSONS[0]), LESSONS[1])
        self.assertIsNone(next_lesson(LESSONS[-1]))


class LessonProgressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Str0ngPass!234",
        )

    def test_progress_starts_empty(self):
        progress = LessonProgress.objects.create(
            user=self.user, lesson_slug="select-columns"
        )

        self.assertEqual(progress.attempts, 0)
        self.assertIsNone(progress.completed_at)

    def test_one_progress_row_per_lesson(self):
        LessonProgress.objects.create(
            user=self.user, lesson_slug="select-columns"
        )

        with self.assertRaises(IntegrityError):
            LessonProgress.objects.create(
                user=self.user, lesson_slug="select-columns"
            )
