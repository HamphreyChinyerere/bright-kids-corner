from django.db import models
from django.contrib.auth.models import User
import uuid

from core.course_images import get_course_thumbnail_url

# ── Existing: Adventure Progress ──────────────────────────────────────────────

class UserAdventureProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    current_node_index = models.IntegerField(default=1)
    total_points_earned = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Adventure Progress"


# ── Existing: Subject Choices ─────────────────────────────────────────────────

SUBJECT_CHOICES = [
    ('Python', 'Python'),
    ('JavaScript', 'JavaScript'),
    ('HTML & CSS', 'HTML & CSS'),
    ('Mathematics', 'Mathematics'),
    ('Physics', 'Physics'),
    ('Chemistry', 'Chemistry'),
    ('Geography', 'Geography'),
    ('Astronomy', 'Astronomy'),
]


# ── Existing: Course & Lesson ─────────────────────────────────────────────────

class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    description = models.TextField(blank=True, default='')
    thumbnail = models.FileField(upload_to='course_thumbnails/', blank=True, null=True)
    instructor_name = models.CharField(max_length=150, blank=True, default='')
    total_chapters = models.IntegerField(default=0)
    total_videos = models.IntegerField(default=0)
    duration_display = models.CharField(max_length=50, blank=True, default='')  # e.g. "2 hr 10 mnts"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('course_detail', kwargs={'slug': self.slug})

    @property
    def thumbnail_display_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return get_course_thumbnail_url(
            subject=self.subject,
            title=self.title,
            slug=self.slug,
        )


class CourseEnrollment(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    progress_percent = models.IntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} → {self.course.title} ({self.status})"


class CourseModule(models.Model):
    """Major topic in a course outline (lessons, exercise, project per module)."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, default='')
    lesson_summary = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Short label for lessons in this topic (e.g. "4 lessons")',
    )
    exercise_title = models.CharField(max_length=255, blank=True, default='')
    exercise_description = models.TextField(blank=True, default='')
    project_title = models.CharField(max_length=255, blank=True, default='')
    project_description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class CourseExam(models.Model):
    """Final exam for a course (synced to Assignments when enrolled)."""
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='final_exam')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    duration_minutes = models.PositiveIntegerField(default=60)

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)
    video_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Task(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='tasks')
    instruction = models.CharField(max_length=500)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Task: {self.instruction[:20]}"


class TaskCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task')


# ── Existing: Projects ────────────────────────────────────────────────────────

PROJECT_TYPE_CHOICES = [
    ('Scratch', 'Scratch'),
    ('WoofJS', 'WoofJS'),
    ('VanillaJS', 'VanillaJS'),
    ('Python', 'Python'),
]

class ProjectSandbox(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255, default="Untitled Project")
    project_type = models.CharField(max_length=50, choices=PROJECT_TYPE_CHOICES)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, related_name='course_projects',
    )
    module = models.ForeignKey(
        CourseModule, on_delete=models.CASCADE, null=True, blank=True, related_name='projects',
    )
    canvas_data_payload = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.project_type})"

    @property
    def is_complete(self):
        return bool(self.canvas_data_payload)


# ── Existing: Assignments ─────────────────────────────────────────────────────

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('In_Progress', 'In Progress'),
    ('Completed', 'Completed'),
]

class AssignmentTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    assignment_title = models.CharField(max_length=255)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    subject_tag = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    assignment_file = models.FileField(upload_to='assignments/', blank=True, null=True)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, related_name='assignment_tasks',
    )
    module = models.ForeignKey(
        CourseModule, on_delete=models.CASCADE, null=True, blank=True, related_name='exercises',
    )
    is_final_exam = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.assignment_title} - {self.user.username}"


# ── Existing: Badges & Certificates ──────────────────────────────────────────

class MilestoneBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge_name = models.CharField(max_length=255)
    badge_type = models.CharField(max_length=50)
    date_unlocked = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.badge_name}"


class VerifiedCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course_name = models.CharField(max_length=255)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date_issued = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate: {self.course_name} for {self.user.username}"


# ── NEW: Calendar ─────────────────────────────────────────────────────────────

EVENT_TYPE_CHOICES = [
    ('lesson', 'Lesson'),
    ('assignment', 'Assignment'),
    ('exam', 'Exam'),
    ('reminder', 'Reminder'),
    ('holiday', 'Holiday'),
]

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='reminder')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(blank=True, null=True)
    all_day = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#FF6B6B')  # hex color
    linked_course = models.ForeignKey(
        Course, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='calendar_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.title} ({self.event_type}) - {self.user.username}"


TIMETABLE_SLOT_TYPES = [
    ('course', 'Course'),
    ('study', 'Study'),
    ('exam', 'Exam'),
    ('break', 'Break'),
    ('custom', 'Custom'),
]

TIMETABLE_SLOT_COLORS = {
    'course': '#E67E66',
    'study': '#71717A',
    'exam': '#C85D44',
    'break': '#8A8A8A',
    'custom': '#F5A623',
}


class TimetableSlot(models.Model):
    """Recurring weekly timetable block (user-adjustable)."""
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timetable_slots')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    title = models.CharField(max_length=255)
    slot_type = models.CharField(max_length=20, choices=TIMETABLE_SLOT_TYPES, default='custom')
    course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_slots',
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time}-{self.end_time}: {self.title}"

    @property
    def color(self):
        return TIMETABLE_SLOT_COLORS.get(self.slot_type, '#E67E66')


# ── NEW: Games ────────────────────────────────────────────────────────────────

class CodingGame(models.Model):
    GAME_TYPES = [
        ('scratch', 'Scratch (MIT Block)'),
        ('woofjs', 'WoofJS (JavaScript Canvas)'),
    ]

    title = models.CharField(max_length=150)
    game_type = models.CharField(max_length=20, choices=GAME_TYPES)
    description = models.TextField(blank=True)
    source_identifier = models.CharField(
        max_length=255,
        help_text='Paste Scratch Project ID OR WoofJS project URL token here',
    )
    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coding_games',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.title} ({self.get_game_type_display()})'

    @property
    def embed_url(self):
        """Resolved iframe src for TurboWarp (Scratch) or WoofJS."""
        raw = (self.source_identifier or '').strip()
        if self.game_type == 'scratch':
            project_id = raw.rstrip('/').split('/')[-1]
            return (
                f'https://turbowarp.org/{project_id}/embed'
                f'?autoplay=false&settings-button=false'
                f'&addons=remove-curved-stage-border,pause'
            )
        return raw


GAME_CATEGORY_CHOICES = [
    ('math', 'Math'),
    ('science', 'Science'),
    ('language', 'Language'),
    ('coding', 'Coding'),
    ('puzzle', 'Puzzle'),
    ('geography', 'Geography'),
    ('general', 'General'),
]

GAME_AGE_GROUP_CHOICES = [
    ('5-8', 'Ages 5–8'),
    ('8-12', 'Ages 8–12'),
    ('12-16', 'Ages 12–16'),
    ('all', 'All Ages'),
]

class EmbeddedGame(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    embed_url = models.URLField()
    thumbnail = models.FileField(upload_to='game_thumbnails/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=GAME_CATEGORY_CHOICES, default='general')
    age_group = models.CharField(max_length=10, choices=GAME_AGE_GROUP_CHOICES, default='all')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    play_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-play_count']

    def __str__(self):
        return f"{self.title} [{self.category}] ({self.age_group})"


class GameSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    game = models.ForeignKey(EmbeddedGame, on_delete=models.CASCADE, related_name='sessions')
    played_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} played {self.game.title}"


# ── NEW: VR Portal ────────────────────────────────────────────────────────────

VR_CONTENT_TYPE_CHOICES = [
    ('360_video', '360° Video'),
    ('webxr', 'WebXR Scene'),
    ('simulation', 'Simulation'),
    ('headset_app', 'Headset App'),
]

class VRContent(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    content_type = models.CharField(max_length=20, choices=VR_CONTENT_TYPE_CHOICES)
    embed_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)       # for 360 videos
    webxr_scene_url = models.URLField(blank=True, null=True) # for WebXR
    thumbnail = models.FileField(upload_to='vr_thumbnails/', blank=True, null=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, blank=True, default='')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    requires_headset = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'title']

    def __str__(self):
        return f"{self.title} [{self.content_type}]"


class VRSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vr_sessions')
    content = models.ForeignKey(VRContent, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.IntegerField(default=0)
    headset_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} → {self.content.title}"