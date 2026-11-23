from django.test import TestCase

from lessons.engine import QueryError, validate_read_only_sql


class SqlValidationTests(TestCase):
    def test_validate_read_only_sql_accepts_cte_with_comments(self):
        sql = "-- report\nWITH top AS (SELECT * FROM students) SELECT * FROM top;"
        validate_read_only_sql(sql)

    def test_validate_read_only_sql_rejects_two_statements(self):
        with self.assertRaisesMessage(QueryError, "one SQL statement"):
            validate_read_only_sql("SELECT * FROM students; SELECT * FROM courses;")

    def test_validate_read_only_sql_rejects_write(self):
        with self.assertRaises(QueryError):
            validate_read_only_sql("DELETE FROM students;")
