from django.core.management.base import BaseCommand

from core.models import Course, CourseExam, CourseModule


class Command(BaseCommand):
    help = 'Create or update the Python Coding course with outline, exercises, and exam.'

    def handle(self, *args, **options):
        course, created = Course.objects.update_or_create(
            slug='python-coding',
            defaults={
                'title': 'Python Coding',
                'subject': 'Python',
                'description': (
                    'Learn Python from scratch — variables, loops, functions, '
                    'data structures, and real-world projects.'
                ),
                'instructor_name': 'Alex Rivera',
                'total_chapters': 12,
                'total_videos': 40,
                'duration_display': '8 hr 30 min',
            },
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} course: {course.title}')

        modules_data = [
            {
                'order': 1,
                'title': 'Getting Started with Python',
                'description': (
                    'Install Python, use the REPL, run your first script, and understand '
                    'how programs are structured.'
                ),
                'lesson_summary': '4 lessons',
                'exercise_title': 'Python Basics — Setup & Hello World',
                'exercise_description': 'Submit a screenshot or .py file showing your first script and environment setup.',
                'project_title': 'Personal Greeting Card (Python)',
                'project_description': 'Build a small script that asks for a name and prints a styled greeting.',
            },
            {
                'order': 2,
                'title': 'Variables, Types & Input/Output',
                'description': (
                    'Work with strings, numbers, booleans, type conversion, and formatted output.'
                ),
                'lesson_summary': '3 lessons',
                'exercise_title': 'Variables & Types Practice Set',
                'exercise_description': 'Complete the worksheet: declare variables, convert types, and format strings.',
                'project_title': 'Unit Converter Mini-App',
                'project_description': 'Create a CLI tool that converts between miles/km or °C/°F.',
            },
            {
                'order': 3,
                'title': 'Conditionals & Loops',
                'description': (
                    'Make decisions with if/elif/else and repeat work with for and while loops.'
                ),
                'lesson_summary': '3 lessons',
                'exercise_title': 'Control Flow Drills',
                'exercise_description': 'Solve 5 branching and loop problems (upload your .py solutions).',
                'project_title': 'Number Guessing Game',
                'project_description': 'Implement a game with hints, attempt limits, and play-again logic.',
            },
            {
                'order': 4,
                'title': 'Functions & Modules',
                'description': (
                    'Define reusable functions, use parameters and return values, and import the standard library.'
                ),
                'lesson_summary': '2 lessons',
                'exercise_title': 'Functions Workbook',
                'exercise_description': 'Refactor repeated code into functions and document with docstrings.',
                'project_title': 'Quiz Generator',
                'project_description': 'Use functions to build a multiple-choice quiz from a question bank.',
            },
            {
                'order': 5,
                'title': 'Lists, Dictionaries & Files',
                'description': (
                    'Store collections of data, read and write files, and handle common data patterns.'
                ),
                'lesson_summary': '3 lessons',
                'exercise_title': 'Data Structures Lab',
                'exercise_description': 'Process a CSV of student scores: averages, top scores, and pass/fail counts.',
                'project_title': 'Expense Tracker',
                'project_description': 'Track expenses in a file; support add, list, and monthly totals.',
            },
        ]

        for data in modules_data:
            order = data.pop('order')
            CourseModule.objects.update_or_create(
                course=course,
                order=order,
                defaults=data,
            )

        CourseExam.objects.update_or_create(
            course=course,
            defaults={
                'title': 'Python Coding — Final Exam',
                'description': (
                    'Comprehensive assessment covering all major topics: syntax, control flow, '
                    'functions, and data structures. Available in Assignments once enrolled.'
                ),
                'duration_minutes': 90,
            },
        )

        self.stdout.write(self.style.SUCCESS('Python course outline ready (slug: python-coding)'))
