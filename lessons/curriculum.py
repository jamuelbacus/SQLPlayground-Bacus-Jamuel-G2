"""Guided lesson definitions.

Lessons are authored here rather than stored in the database. Each one teaches
a single concept, gives the learner a task, and checks the result against a
reference query run by the practice engine.
"""

from __future__ import annotations

from dataclasses import dataclass

LEVELS = ("Beginner", "Intermediate", "Advanced")


@dataclass(frozen=True)
class Lesson:
    slug: str
    order: int
    level: str
    title: str
    summary: str
    concept: str
    objective: str
    task: str
    starter_sql: str
    reference_sql: str
    ordered: bool
    hint: str
    success_message: str


LESSONS = (
    Lesson(
        slug="select-columns",
        order=1,
        level="Beginner",
        title="Choose columns with SELECT",
        summary="Return only the columns you need from a table.",
        concept="SELECT",
        objective="Read rows from a table and choose specific columns.",
        task=(
            "Show each student's first name and last name from the students "
            "table."
        ),
        starter_sql="SELECT *\nFROM students;",
        reference_sql="SELECT first_name, last_name FROM students;",
        ordered=False,
        hint=(
            "Replace the star with the two column names, separated by a comma, "
            "after SELECT."
        ),
        success_message="Correct. You selected just the columns the task asked for.",
    ),
    Lesson(
        slug="filter-rows",
        order=2,
        level="Beginner",
        title="Filter rows with WHERE",
        summary="Keep only the rows that match a condition.",
        concept="WHERE",
        objective="Use a WHERE clause to return a subset of rows.",
        task="Show the first and last name of students who enrolled in 2024.",
        starter_sql="SELECT first_name, last_name\nFROM students;",
        reference_sql=(
            "SELECT first_name, last_name FROM students "
            "WHERE enrollment_year = 2024;"
        ),
        ordered=False,
        hint="Add WHERE enrollment_year = 2024 before the semicolon.",
        success_message="Correct. Your WHERE clause kept only 2024 students.",
    ),
    Lesson(
        slug="sort-limit",
        order=3,
        level="Beginner",
        title="Sort and limit results",
        summary="Order rows and keep only the top few.",
        concept="ORDER BY, LIMIT",
        objective="Sort a result set and cap the number of rows returned.",
        task=(
            "Show the first name, last name, and enrollment year of the three "
            "most recent students. Sort newest year first, then by first name, "
            "and return only three rows."
        ),
        starter_sql="SELECT first_name, last_name, enrollment_year\nFROM students;",
        reference_sql=(
            "SELECT first_name, last_name, enrollment_year FROM students "
            "ORDER BY enrollment_year DESC, first_name ASC LIMIT 3;"
        ),
        ordered=True,
        hint=(
            "Use ORDER BY enrollment_year DESC, first_name ASC before LIMIT 3."
        ),
        success_message="Correct. The rows are sorted and capped at three.",
    ),
    Lesson(
        slug="count-group",
        order=4,
        level="Intermediate",
        title="Count rows with GROUP BY",
        summary="Summarize rows into groups with an aggregate.",
        concept="COUNT, GROUP BY",
        objective="Group rows and count how many rows fall into each group.",
        task=(
            "Show each enrollment year and the number of students in that year. "
            "Name the count column total and sort by year, oldest first."
        ),
        starter_sql=(
            "SELECT enrollment_year, COUNT(*)\nFROM students\n"
            "GROUP BY enrollment_year;"
        ),
        reference_sql=(
            "SELECT enrollment_year, COUNT(*) AS total FROM students "
            "GROUP BY enrollment_year ORDER BY enrollment_year;"
        ),
        ordered=True,
        hint=(
            "GROUP BY enrollment_year, use COUNT(*) AS total, then ORDER BY "
            "enrollment_year."
        ),
        success_message="Correct. You grouped the students and counted each group.",
    ),
    Lesson(
        slug="join-three-tables",
        order=5,
        level="Intermediate",
        title="Join related tables",
        summary="Combine rows from students, enrollments, and courses.",
        concept="JOIN",
        objective="Join three tables using their matching id columns.",
        task=(
            "Show each student's first name, last name, course name, and grade. "
            "Sort by last name, then by course name."
        ),
        starter_sql=(
            "SELECT s.first_name, s.last_name, c.course_name, e.grade\n"
            "FROM enrollments e\n"
            "JOIN students s ON s.student_id = e.student_id\n"
            "JOIN courses c ON c.course_id = e.course_id;"
        ),
        reference_sql=(
            "SELECT s.first_name, s.last_name, c.course_name, e.grade "
            "FROM enrollments e "
            "JOIN students s ON s.student_id = e.student_id "
            "JOIN courses c ON c.course_id = e.course_id "
            "ORDER BY s.last_name, c.course_name;"
        ),
        ordered=True,
        hint=(
            "Join enrollments to students on student_id and to courses on "
            "course_id, then add ORDER BY s.last_name, c.course_name."
        ),
        success_message="Correct. The three tables are joined and sorted.",
    ),
    Lesson(
        slug="left-join",
        order=6,
        level="Intermediate",
        title="Keep unmatched rows with LEFT JOIN",
        summary="Include students who have no enrollments yet.",
        concept="LEFT JOIN",
        objective="Use a LEFT JOIN so rows without a match still appear.",
        task=(
            "Show every student's first name, last name, and number of enrolled "
            "courses. Include students with no courses. Name the count column "
            "courses and sort by student id."
        ),
        starter_sql=(
            "SELECT s.first_name, s.last_name, COUNT(e.enrollment_id)\n"
            "FROM students s\n"
            "LEFT JOIN enrollments e ON e.student_id = s.student_id\n"
            "GROUP BY s.student_id;"
        ),
        reference_sql=(
            "SELECT s.first_name, s.last_name, "
            "COUNT(e.enrollment_id) AS courses "
            "FROM students s "
            "LEFT JOIN enrollments e ON e.student_id = s.student_id "
            "GROUP BY s.student_id, s.first_name, s.last_name "
            "ORDER BY s.student_id;"
        ),
        ordered=True,
        hint=(
            "COUNT the enrollment id, not the star. A LEFT JOIN keeps the "
            "student row even when there is no match."
        ),
        success_message="Correct. Students without courses still appear with zero.",
    ),
    Lesson(
        slug="having-aggregates",
        order=7,
        level="Advanced",
        title="Filter groups with HAVING",
        summary="Keep only the groups that meet an aggregate condition.",
        concept="HAVING, SUM",
        objective="Filter grouped rows with HAVING and an aggregate function.",
        task=(
            "Show the first name, last name, and total credits for students "
            "whose enrolled courses add up to more than 4 credits. Name the "
            "total column total_credits and sort highest first."
        ),
        starter_sql=(
            "SELECT s.first_name, s.last_name, SUM(c.credits)\n"
            "FROM students s\n"
            "JOIN enrollments e ON e.student_id = s.student_id\n"
            "JOIN courses c ON c.course_id = e.course_id\n"
            "GROUP BY s.student_id;"
        ),
        reference_sql=(
            "SELECT s.first_name, s.last_name, "
            "SUM(c.credits) AS total_credits "
            "FROM students s "
            "JOIN enrollments e ON e.student_id = s.student_id "
            "JOIN courses c ON c.course_id = e.course_id "
            "GROUP BY s.student_id, s.first_name, s.last_name "
            "HAVING SUM(c.credits) > 4 "
            "ORDER BY total_credits DESC;"
        ),
        ordered=True,
        hint=(
            "After GROUP BY, add HAVING SUM(c.credits) > 4 and sort by the "
            "total descending."
        ),
        success_message="Correct. HAVING removed the smaller totals.",
    ),
    Lesson(
        slug="subquery",
        order=8,
        level="Advanced",
        title="Find rows with a subquery",
        summary="Use a query inside another query to find missing links.",
        concept="Subquery, NOT IN",
        objective="Use a subquery to compare one table against another.",
        task=(
            "Show the first and last name of students who are not enrolled in "
            "any course. Sort by last name."
        ),
        starter_sql=(
            "SELECT first_name, last_name\nFROM students\n"
            "WHERE student_id NOT IN (SELECT student_id FROM enrollments);"
        ),
        reference_sql=(
            "SELECT first_name, last_name FROM students "
            "WHERE student_id NOT IN (SELECT student_id FROM enrollments) "
            "ORDER BY last_name;"
        ),
        ordered=True,
        hint=(
            "The subquery should select student_id from enrollments. Use NOT IN "
            "to keep students outside that list."
        ),
        success_message="Correct. Your subquery found the unenrolled student.",
    ),
)

LESSONS_BY_SLUG = {lesson.slug: lesson for lesson in LESSONS}


def lessons_for_level(level: str) -> list[Lesson]:
    return [lesson for lesson in LESSONS if lesson.level == level]


def next_lesson(lesson: Lesson) -> Lesson | None:
    for candidate in LESSONS:
        if candidate.order == lesson.order + 1:
            return candidate
    return None
