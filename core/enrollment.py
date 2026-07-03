"""Course enrollment: create linked assignments, projects, and track progress."""

from datetime import date, timedelta

from django.db import transaction

from .models import (
    AssignmentTask,
    Course,
    CourseEnrollment,
    CourseExam,
    ProjectSandbox,
)


FEATURED_CATALOG_SLUGS = frozenset({'python-coding'})


def enroll_user_in_course(user, course: Course) -> CourseEnrollment:
    """Enroll user and sync module exercises, projects, and final exam to sidebar pages."""
    with transaction.atomic():
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=user,
            course=course,
            defaults={'status': 'ongoing', 'progress_percent': 0},
        )
        if not created and enrollment.status != 'ongoing':
            enrollment.status = 'ongoing'
            enrollment.save(update_fields=['status'])

        _sync_course_work_items(user, course)
        update_enrollment_progress(enrollment)
        return enrollment


def _sync_course_work_items(user, course: Course) -> None:
    """Create assignment and project rows for each module + final exam."""
    base_due = date.today() + timedelta(days=14)
    subject = course.subject

    for index, module in enumerate(course.modules.all()):
        due = base_due + timedelta(days=7 * index)
        if module.exercise_title:
            AssignmentTask.objects.get_or_create(
                user=user,
                course=course,
                module=module,
                is_final_exam=False,
                defaults={
                    'assignment_title': module.exercise_title,
                    'due_date': due,
                    'status': 'Pending',
                    'subject_tag': subject,
                },
            )
        if module.project_title:
            ProjectSandbox.objects.get_or_create(
                user=user,
                course=course,
                module=module,
                defaults={
                    'title': module.project_title,
                    'project_type': 'Python' if subject == 'Python' else 'VanillaJS',
                    'canvas_data_payload': {},
                },
            )

    try:
        exam = course.final_exam
    except CourseExam.DoesNotExist:
        exam = None

    if exam:
        AssignmentTask.objects.get_or_create(
            user=user,
            course=course,
            is_final_exam=True,
            defaults={
                'assignment_title': exam.title,
                'due_date': base_due + timedelta(days=7 * course.modules.count()),
                'status': 'Pending',
                'subject_tag': subject,
                'module': None,
            },
        )


def update_enrollment_progress(enrollment: CourseEnrollment) -> None:
    """Recalculate progress from completed exercises, projects, and exam."""
    user = enrollment.user
    course = enrollment.course
    total = 0
    completed = 0

    for module in course.modules.all():
        if module.exercise_title:
            total += 1
            if AssignmentTask.objects.filter(
                user=user, module=module, status='Completed',
            ).exists():
                completed += 1
        if module.project_title:
            total += 1
            project = ProjectSandbox.objects.filter(user=user, module=module).first()
            if project and project.canvas_data_payload:
                completed += 1

    if hasattr(course, 'final_exam'):
        total += 1
        if AssignmentTask.objects.filter(
            user=user, course=course, is_final_exam=True, status='Completed',
        ).exists():
            completed += 1

    progress = int((completed / total) * 100) if total else 0
    enrollment.progress_percent = progress
    enrollment.status = 'completed' if progress >= 100 else 'ongoing'
    enrollment.save(update_fields=['progress_percent', 'status'])


def get_module_progress(user, course: Course) -> list:
    """Outline rows with completion flags for the course detail page."""
    rows = []
    for module in course.modules.all():
        exercise_done = False
        project_done = False
        exercise_id = None
        project_id = None

        if module.exercise_title:
            ex = AssignmentTask.objects.filter(user=user, module=module).first()
            if ex:
                exercise_id = ex.id
                exercise_done = ex.status == 'Completed'
        if module.project_title:
            proj = ProjectSandbox.objects.filter(user=user, module=module).first()
            if proj:
                project_id = proj.id
                project_done = bool(proj.canvas_data_payload)

        rows.append({
            'module': module,
            'exercise_done': exercise_done,
            'project_done': project_done,
            'exercise_id': exercise_id,
            'project_id': project_id,
        })

    exam_done = False
    exam_id = None
    if hasattr(course, 'final_exam'):
        exam = AssignmentTask.objects.filter(
            user=user, course=course, is_final_exam=True,
        ).first()
        if exam:
            exam_id = exam.id
            exam_done = exam.status == 'Completed'

    return rows, exam_done, exam_id
