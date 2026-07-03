from django.views.generic import TemplateView, ListView, DetailView
from django.views import View
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django import forms
from django.db.models import Q, Sum, Prefetch
from django.urls import reverse
import json
import calendar
from datetime import date, datetime, time, timedelta

from django.utils.dateparse import parse_date, parse_datetime

from .models import (
    UserAdventureProgress, Course, CourseEnrollment, Lesson, Task, TaskCompletion,
    ProjectSandbox, AssignmentTask, MilestoneBadge, VerifiedCertificate,
    CalendarEvent, TimetableSlot, EmbeddedGame, CodingGame, GameSession, VRContent,
    CourseModule,
)
from .forms import AssignmentUploadForm
from .enrollment import (
    FEATURED_CATALOG_SLUGS,
    enroll_user_in_course,
    get_module_progress,
    update_enrollment_progress,
)


class AuthForm(forms.Form):
    """Universal auth form for both login and signup."""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full edu-input px-4 py-3 font-medium text-[#1A1A1A] transition-all',
        'placeholder': 'Username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full edu-input px-4 py-3 font-medium text-[#1A1A1A] transition-all',
        'placeholder': 'Password',
    }))
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={
        'class': 'w-full edu-input px-4 py-3 font-medium text-[#1A1A1A] transition-all',
        'placeholder': 'Confirm password (for new accounts)',
    }))

    def __init__(self, *args, **kwargs):
        self.user_exists = kwargs.pop('user_exists', False)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if not self.user_exists and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")

        return cleaned_data


class HomeRedirectView(View):
    """Redirect home to login or dashboard depending on authentication state."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return redirect('/auth/?mode=login')


class AuthView(View):
    """Unified authentication view for login and signup."""
    template_name = 'auth.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        mode = request.GET.get('mode', 'login')
        if mode not in ('login', 'signup'):
            mode = 'login'
        form = AuthForm()
        return render(request, self.template_name, {'form': form, 'mode': mode})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        mode = request.POST.get('mode', 'signup')
        if mode not in ('login', 'signup'):
            mode = 'signup'

        from django.contrib.auth.models import User
        user_exists = User.objects.filter(username=username).exists()

        form = AuthForm(request.POST, user_exists=user_exists)

        if form.is_valid():
            if mode == 'login':
                if not user_exists:
                    form.add_error(None, 'Username not found. Please create an account.')
                    return render(request, self.template_name, {'form': form, 'mode': 'login', 'username': username})

                user = authenticate(username=username, password=password)
                if user is not None:
                    auth_login(request, user)
                    return redirect('dashboard')

                form.add_error(None, 'Invalid username or password.')
                return render(request, self.template_name, {'form': form, 'mode': 'login', 'username': username})

            if mode == 'signup':
                if user_exists:
                    form.add_error(None, 'Username already exists. Please sign in.')
                    return render(request, self.template_name, {'form': form, 'mode': 'signup', 'username': username})

                if not confirm_password:
                    form.add_error('confirm_password', 'Please confirm your password.')
                    return render(request, self.template_name, {'form': form, 'mode': 'signup', 'username': username})

                try:
                    user = User.objects.create_user(username=username, password=password)
                    auth_login(request, user)
                    return redirect('dashboard')
                except Exception as e:
                    form.add_error(None, str(e))
                    return render(request, self.template_name, {'form': form, 'mode': 'signup', 'username': username})

        return render(request, self.template_name, {'form': form, 'mode': mode, 'username': username})


def check_username_exists(request):
    """API endpoint to check if username exists."""
    username = request.GET.get('username', '').strip()
    from django.contrib.auth.models import User
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})


class SignupView(View):
    """Deprecated: Use AuthView instead."""
    def get(self, request):
        return redirect('auth')

    def post(self, request):
        return redirect('auth')


# ── Existing: Dashboard ───────────────────────────────────────────────────────

class DashboardMapView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_streamlined_view'] = self.request.session.get('is_streamlined_view', False)

        progress, created = UserAdventureProgress.objects.get_or_create(user=self.request.user)
        context['progress'] = progress

        nodes = []
        for i in range(1, 11):
            if i < progress.current_node_index:
                status = 'completed'
            elif i == progress.current_node_index:
                status = 'active'
            else:
                status = 'locked'
            nodes.append({'index': i, 'status': status})

        context['adventure_nodes'] = nodes

        # Recent enrollments for dashboard widget
        context['recent_enrollments'] = CourseEnrollment.objects.filter(
            user=self.request.user
        ).select_related('course').order_by('-enrolled_at')[:4]

        # Upcoming calendar events
        context['upcoming_events'] = CalendarEvent.objects.filter(
            user=self.request.user,
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')[:5]

        return context


# ── Existing: Courses ─────────────────────────────────────────────────────────

class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        user = self.request.user

        context.update({
            'query': query,
            'courses': Course.objects.none(),
            'embedded_games': EmbeddedGame.objects.none(),
            'coding_games': CodingGame.objects.none(),
            'assignments': AssignmentTask.objects.none(),
            'projects': ProjectSandbox.objects.none(),
            'vr_content': VRContent.objects.none(),
            'total_results': 0,
        })

        if not query:
            return context

        courses = Course.objects.filter(
            Q(title__icontains=query) |
            Q(subject__icontains=query) |
            Q(description__icontains=query) |
            Q(instructor_name__icontains=query)
        ).distinct()[:8]
        embedded_games = EmbeddedGame.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(age_group__icontains=query),
            is_active=True,
        ).distinct()[:8]
        coding_games = CodingGame.objects.select_related(
            'module', 'module__course',
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(game_type__icontains=query) |
            Q(module__title__icontains=query) |
            Q(module__course__title__icontains=query)
        ).distinct()[:8]
        assignments = AssignmentTask.objects.select_related(
            'course', 'module',
        ).filter(
            Q(assignment_title__icontains=query) |
            Q(subject_tag__icontains=query) |
            Q(course__title__icontains=query) |
            Q(module__title__icontains=query),
            user=user,
        ).distinct()[:8]
        projects = ProjectSandbox.objects.select_related(
            'course', 'module',
        ).filter(
            Q(title__icontains=query) |
            Q(project_type__icontains=query) |
            Q(course__title__icontains=query) |
            Q(module__title__icontains=query),
            user=user,
        ).distinct()[:8]
        vr_content = VRContent.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(subject__icontains=query) |
            Q(content_type__icontains=query),
            is_active=True,
        ).distinct()[:8]

        context.update({
            'courses': courses,
            'embedded_games': embedded_games,
            'coding_games': coding_games,
            'assignments': assignments,
            'projects': projects,
            'vr_content': vr_content,
            'total_results': (
                len(courses) + len(embedded_games) + len(coding_games) +
                len(assignments) + len(projects) + len(vr_content)
            ),
        })
        return context


class CourseListView(LoginRequiredMixin, TemplateView):
    template_name = 'course_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        filter_tab = self.request.GET.get('filter', 'all')
        context['filter_tab'] = filter_tab

        enrolled_ids = CourseEnrollment.objects.filter(
            user=user
        ).values_list('course_id', flat=True)

        all_courses = Course.objects.all()

        # Attach enrollment info to each course
        enrollments = {
            e.course_id: e for e in CourseEnrollment.objects.filter(user=user)
        }

        courses_with_status = []
        for course in all_courses:
            if filter_tab == 'all' and course.slug in FEATURED_CATALOG_SLUGS:
                continue
            enrollment = enrollments.get(course.id)
            courses_with_status.append({
                'course': course,
                'enrollment': enrollment,
                'status': enrollment.status if enrollment else 'not_enrolled',
                'progress': enrollment.progress_percent if enrollment else 0,
            })

        python_course = Course.objects.filter(slug='python-coding').first()
        python_enrollment = None
        if python_course:
            python_enrollment = enrollments.get(python_course.id)
        context['python_course'] = python_course
        context['python_enrollment'] = python_enrollment

        if filter_tab == 'ongoing':
            courses_with_status = [c for c in courses_with_status if c['status'] == 'ongoing']
        elif filter_tab == 'completed':
            courses_with_status = [c for c in courses_with_status if c['status'] == 'completed']

        context['courses_with_status'] = courses_with_status
        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'course_outline.html'
    context_object_name = 'course'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Course.objects.prefetch_related(
            Prefetch(
                'modules',
                queryset=CourseModule.objects.prefetch_related('coding_games'),
            ),
        ).select_related('final_exam')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user

        enrollment = CourseEnrollment.objects.filter(user=user, course=course).first()
        context['enrollment'] = enrollment
        context['is_enrolled'] = enrollment is not None

        module_rows, exam_done, exam_id = get_module_progress(user, course)
        context['module_rows'] = module_rows
        context['exam_done'] = exam_done
        context['exam_id'] = exam_id
        context['final_exam'] = getattr(course, 'final_exam', None)
        context['just_enrolled'] = self.request.GET.get('enrolled') == '1'
        return context

    def post(self, request, *args, **kwargs):
        course = self.get_object()
        if request.POST.get('action') == 'enroll':
            enroll_user_in_course(request.user, course)
            return redirect(f"{course.get_absolute_url()}?enrolled=1")
        return redirect(course.get_absolute_url())


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'course_detail.html'
    context_object_name = 'lesson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        user = self.request.user

        tasks = lesson.tasks.all()
        completed_task_ids = set(
            TaskCompletion.objects.filter(
                user=user, task__in=tasks
            ).values_list('task_id', flat=True)
        )

        task_list = []
        for task in tasks:
            task_list.append({
                'task': task,
                'is_completed': task.id in completed_task_ids
            })

        context['tasks_with_status'] = task_list

        # Sidebar: other lessons in same course
        context['course_lessons'] = lesson.course.lessons.all()
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                task_id = data.get('task_id')
                task = get_object_or_404(Task, id=task_id)
                user = request.user

                completion, created = TaskCompletion.objects.get_or_create(user=user, task=task)

                if created:
                    progress, _ = UserAdventureProgress.objects.get_or_create(user=user)
                    progress.total_points_earned += 10
                    progress.save()

                return JsonResponse({
                    'status': 'success',
                    'points': user.progress.total_points_earned
                })
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ── Existing: Projects ────────────────────────────────────────────────────────

class ProjectsHubListView(LoginRequiredMixin, TemplateView):
    template_name = 'games_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        course_slug = self.request.GET.get('course')

        context['scratch_projects'] = ProjectSandbox.objects.filter(
            user=user, project_type='Scratch', course__isnull=True,
        ).order_by('-updated_at')
        context['text_projects'] = ProjectSandbox.objects.filter(
            user=user, project_type__in=['WoofJS', 'VanillaJS'], course__isnull=True,
        ).order_by('-updated_at')

        enrolled_courses = Course.objects.filter(
            enrollments__user=user,
        ).distinct().order_by('title')

        course_tiles = []
        for course in enrolled_courses:
            projects = list(
                ProjectSandbox.objects.filter(user=user, course=course).select_related('module')
            )
            course_tiles.append({
                'course': course,
                'ongoing_count': sum(1 for p in projects if not p.is_complete),
                'finished_count': sum(1 for p in projects if p.is_complete),
                'total': len(projects),
            })

        context['course_tiles'] = course_tiles
        context['selected_course'] = None
        context['ongoing_projects'] = []
        context['finished_projects'] = []

        if course_slug:
            course = Course.objects.filter(
                slug=course_slug, enrollments__user=user,
            ).first()
            if course:
                all_projects = list(
                    ProjectSandbox.objects.filter(user=user, course=course)
                    .select_related('module')
                )
                sort_key = lambda p: (p.module.order if p.module else 999, p.title)
                context['selected_course'] = course
                context['ongoing_projects'] = sorted(
                    [p for p in all_projects if not p.is_complete], key=sort_key,
                )
                context['finished_projects'] = sorted(
                    [p for p in all_projects if p.is_complete], key=sort_key,
                )

        sandbox_tiles = [
            {
                'slug': 'scratch',
                'title': 'Visual Block (Scratch)',
                'subject': 'Creative Coding',
                'icon': '🧩',
                'count': context['scratch_projects'].count(),
            },
            {
                'slug': 'text',
                'title': 'Text-Based Sandboxes',
                'subject': 'JavaScript & WoofJS',
                'icon': '💻',
                'count': context['text_projects'].count(),
            },
        ]
        context['sandbox_tiles'] = sandbox_tiles
        context['sandbox_view'] = self.request.GET.get('sandbox')
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                action = data.get('action')
                project_id = data.get('project_id')

                if action == 'save':
                    payload = data.get('payload', {})
                    title = data.get('title', 'Untitled Project')
                    project_type = data.get('project_type', 'Scratch')

                    if project_id:
                        project = get_object_or_404(
                            ProjectSandbox, id=project_id, user=request.user
                        )
                        if data.get('title'):
                            project.title = title
                        project.canvas_data_payload = payload
                        project.save()
                        if project.course_id:
                            enrollment = CourseEnrollment.objects.filter(
                                user=request.user, course_id=project.course_id,
                            ).first()
                            if enrollment:
                                update_enrollment_progress(enrollment)
                    else:
                        project = ProjectSandbox.objects.create(
                            user=request.user,
                            title=title,
                            project_type=project_type,
                            canvas_data_payload=payload
                        )
                    return JsonResponse({'status': 'success', 'project_id': project.id})

                elif action == 'publish':
                    project = get_object_or_404(
                        ProjectSandbox, id=project_id, user=request.user
                    )
                    project.is_public = True
                    project.save()
                    if project.course_id:
                        enrollment = CourseEnrollment.objects.filter(
                            user=request.user, course_id=project.course_id,
                        ).first()
                        if enrollment:
                            update_enrollment_progress(enrollment)
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Project published to Public Arcade!'
                    })

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ── Existing: Assignments ─────────────────────────────────────────────────────

class AssignmentWorkspaceView(LoginRequiredMixin, TemplateView):
    template_name = 'assignment_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_streamlined_view'] = self.request.session.get('is_streamlined_view', False)
        context['pending_tasks'] = AssignmentTask.objects.filter(
            user=user, status='Pending'
        ).order_by('due_date')
        context['in_progress_tasks'] = AssignmentTask.objects.filter(
            user=user, status='In_Progress'
        ).order_by('due_date')
        context['completed_tasks'] = AssignmentTask.objects.filter(
            user=user, status='Completed'
        ).order_by('-due_date')
        if 'form' not in context:
            context['form'] = AssignmentUploadForm()
        return context

    def post(self, request, *args, **kwargs):
        task_id = request.POST.get('task_id')
        if task_id:
            task = get_object_or_404(AssignmentTask, id=task_id, user=request.user)
            form = AssignmentUploadForm(request.POST, request.FILES, instance=task)
            if form.is_valid():
                assignment = form.save(commit=False)
                assignment.status = 'Completed'
                assignment.save()
                if assignment.course_id:
                    enrollment = CourseEnrollment.objects.filter(
                        user=request.user, course_id=assignment.course_id,
                    ).first()
                    if enrollment:
                        update_enrollment_progress(enrollment)
                return redirect('assignment_workspace')
            context = self.get_context_data()
            context['form'] = form
            context['active_tab'] = request.POST.get('active_tab', 'pending')
            return self.render_to_response(context)
        return redirect('assignment_workspace')


# ── Existing: Rewards & Certificates ─────────────────────────────────────────

class CertificationsView(LoginRequiredMixin, TemplateView):
    template_name = 'certifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        for enrollment in CourseEnrollment.objects.filter(user=user, status='completed').select_related('course'):
            VerifiedCertificate.objects.get_or_create(
                user=user,
                course_name=enrollment.course.title,
            )

        context['certificates'] = VerifiedCertificate.objects.filter(
            user=user,
        ).order_by('-date_issued')

        context['in_progress_courses'] = CourseEnrollment.objects.filter(
            user=user, status='ongoing',
        ).select_related('course').order_by('-enrolled_at')

        return context


class RewardsVaultView(LoginRequiredMixin, TemplateView):
    template_name = 'rewards_vault.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        all_badges = [
            {'name': 'First Steps',    'desc': 'Complete your first course',      'color': '#FFD166'},
            {'name': '7-Day Streak',   'desc': 'Log in for 7 consecutive days',   'color': '#06D6A0'},
            {'name': 'Project Master', 'desc': 'Publish 3 projects',              'color': '#FF6B6B'},
            {'name': 'Code Wizard',    'desc': 'Finish the Python path',          'color': '#118AB2'},
            {'name': 'Speed Learner',  'desc': 'Finish 5 lessons in one day',     'color': '#073B4C'},
            {'name': 'VR Explorer',    'desc': 'Complete a VR session',           'color': '#9B5DE5'},
            {'name': 'Game Champion',  'desc': 'Play 10 educational games',       'color': '#F15BB5'},
            {'name': 'Calendar Hero',  'desc': 'Add 5 events to your calendar',   'color': '#00BBF9'},
        ]

        earned_badge_names = list(
            MilestoneBadge.objects.filter(user=user).values_list('badge_name', flat=True)
        )

        badges = []
        for b in all_badges:
            b_copy = b.copy()
            b_copy['earned'] = b['name'] in earned_badge_names
            badges.append(b_copy)

        context['badges'] = badges
        context['certificates'] = VerifiedCertificate.objects.filter(
            user=user
        ).order_by('-date_issued')
        return context


class CertificatePDFExportView(LoginRequiredMixin, View):
    def get(self, request, token, *args, **kwargs):
        cert = get_object_or_404(VerifiedCertificate, token=token, user=request.user)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="certificate_{cert.course_name.replace(" ", "_")}.pdf"'
        )

        try:
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors

            p = rl_canvas.Canvas(response, pagesize=letter)
            width, height = letter

            p.setStrokeColor(colors.HexColor('#073B4C'))
            p.setLineWidth(4)
            p.rect(20, 20, width - 40, height - 40)
            p.setStrokeColor(colors.HexColor('#FFD166'))
            p.setLineWidth(2)
            p.rect(25, 25, width - 50, height - 50)

            p.setFont("Helvetica-Bold", 36)
            p.setFillColor(colors.HexColor('#073B4C'))
            p.drawCentredString(width / 2.0, height - 120, "Certificate of Completion")

            p.setFont("Helvetica", 18)
            p.drawCentredString(width / 2.0, height - 200, "This officially certifies that")

            p.setFont("Helvetica-Bold", 28)
            p.setFillColor(colors.HexColor('#FF6B6B'))
            p.drawCentredString(width / 2.0, height - 260, f"{cert.user.username}")

            p.setFont("Helvetica", 18)
            p.setFillColor(colors.HexColor('#073B4C'))
            p.drawCentredString(
                width / 2.0, height - 320, "has successfully mastered the coursework for"
            )

            p.setFont("Helvetica-Bold", 24)
            p.setFillColor(colors.HexColor('#06D6A0'))
            p.drawCentredString(width / 2.0, height - 380, f"{cert.course_name}")

            p.setFont("Helvetica", 14)
            p.setFillColor(colors.HexColor('#073B4C'))
            p.drawCentredString(
                width / 2.0, height - 500,
                f"Awarded on: {cert.date_issued.strftime('%B %d, %Y')}"
            )

            p.setFont("Helvetica-Oblique", 10)
            p.drawCentredString(
                width / 2.0, height - 550,
                f"Official Verification Token: {cert.token}"
            )

            p.showPage()
            p.save()
        except ImportError:
            response.write(b"PDF generation library not available.")

        return response


# ── Existing: VR (updated) ────────────────────────────────────────────────────

class VRHardwareControllerView(LoginRequiredMixin, TemplateView):
    """Main VR portal landing — shows all 4 sub-sections."""
    template_name = 'vr_portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sync_token = self.request.GET.get('sync_token')
        context['vr_device_connected'] = (sync_token == 'valid_hardware_123')

        # Counts for each section
        context['count_360']        = VRContent.objects.filter(content_type='360_video',   is_active=True).count()
        context['count_webxr']      = VRContent.objects.filter(content_type='webxr',       is_active=True).count()
        context['count_simulation'] = VRContent.objects.filter(content_type='simulation',  is_active=True).count()
        context['count_headset']    = VRContent.objects.filter(content_type='headset_app', is_active=True).count()
        context['featured_vr']      = VRContent.objects.filter(is_featured=True, is_active=True)[:3]
        return context


class VR360VideoView(LoginRequiredMixin, TemplateView):
    template_name = 'vr_360.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['videos'] = VRContent.objects.filter(
            content_type='360_video', is_active=True
        ).order_by('-is_featured')
        return context


class VRWebXRView(LoginRequiredMixin, TemplateView):
    template_name = 'vr_webxr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['scenes'] = VRContent.objects.filter(
            content_type='webxr', is_active=True
        ).order_by('-is_featured')
        return context


class VRComingSoonView(LoginRequiredMixin, TemplateView):
    template_name = 'vr_coming_soon.html'


class VRSpaceSimulationView(LoginRequiredMixin, TemplateView):
    template_name = 'vr_space_simulation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['simulations'] = VRContent.objects.filter(
            content_type='simulation', is_active=True
        ).order_by('-is_featured')
        return context


# ── Existing: Toggle & Profile ────────────────────────────────────────────────

def toggle_view_density(request):
    if request.method == 'POST':
        current_state = request.session.get('is_streamlined_view', False)
        request.session['is_streamlined_view'] = not current_state
    return redirect(request.META.get('HTTP_REFERER', '/'))


class ProfileHubView(LoginRequiredMixin, TemplateView):
    template_name = 'profile_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['training_hours'] = [
            {'day': 'Mon', 'hours': 2, 'height': '40%'},
            {'day': 'Tue', 'hours': 3, 'height': '60%'},
            {'day': 'Wed', 'hours': 1, 'height': '20%'},
            {'day': 'Thu', 'hours': 5, 'height': '100%'},
            {'day': 'Fri', 'hours': 4, 'height': '80%'},
            {'day': 'Sat', 'hours': 0, 'height': '5%'},
            {'day': 'Sun', 'hours': 2, 'height': '40%'},
        ]
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')

        if first_name is not None: user.first_name = first_name
        if last_name  is not None: user.last_name  = last_name
        if email      is not None: user.email      = email

        user.save()
        return redirect('profile_hub')


class KidsModeView(LoginRequiredMixin, TemplateView):
    template_name = 'kids_mode.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_streamlined_view'] = self.request.session.get('is_streamlined_view', False)
        return context


# ── Calendar ──────────────────────────────────────────────────────────────────

CALENDAR_EVENT_COLORS = {
    'lesson': '#E67E66',
    'assignment': '#F5A623',
    'exam': '#C85D44',
    'reminder': '#71717A',
    'holiday': '#8A8A8A',
}


def _parse_event_datetime(value, default_date=None):
    """Parse ISO datetime or date string into timezone-aware datetime."""
    if not value:
        if default_date:
            return timezone.make_aware(datetime.combine(default_date, time(9, 0)))
        return timezone.now()
    parsed = parse_datetime(value)
    if parsed:
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed)
        return parsed
    d = parse_date(value)
    if d:
        return timezone.make_aware(datetime.combine(d, time(9, 0)))
    return timezone.now()


def _parse_time_value(value):
    if not value:
        return time(9, 0)
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return time(9, 0)


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        today = date.today()
        year = int(self.request.GET.get('year', today.year))
        month = int(self.request.GET.get('month', today.month))

        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]

        events = CalendarEvent.objects.filter(
            user=user,
            start_datetime__year=year,
            start_datetime__month=month,
        ).select_related('linked_course').order_by('start_datetime')

        events_by_day = {}
        for event in events:
            events_by_day.setdefault(event.start_datetime.day, []).append(event)

        deadlines_by_day = {}
        for task in AssignmentTask.objects.filter(user=user).select_related('course'):
            if task.due_date.year == year and task.due_date.month == month:
                deadlines_by_day.setdefault(task.due_date.day, []).append(task)

        prev_month = month - 1 or 12
        prev_year = year - 1 if month == 1 else year
        next_month = month + 1 if month < 12 else 1
        next_year = year + 1 if month == 12 else year

        timetable_slots = TimetableSlot.objects.filter(user=user).select_related('course')
        timetable_by_day = {i: [] for i in range(7)}
        for slot in timetable_slots:
            timetable_by_day[slot.weekday].append(slot)

        enrolled_courses = Course.objects.filter(
            enrollments__user=user,
        ).distinct().order_by('title')

        events_payload = []
        for event in events:
            events_payload.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'event_type': event.event_type,
                'day': event.start_datetime.day,
                'start': event.start_datetime.isoformat(),
                'end': event.end_datetime.isoformat() if event.end_datetime else None,
                'color': event.color or CALENDAR_EVENT_COLORS.get(event.event_type, '#E67E66'),
                'course': event.linked_course.title if event.linked_course else '',
                'all_day': event.all_day,
            })

        deadlines_payload = []
        for task in AssignmentTask.objects.filter(user=user).select_related('course'):
            deadlines_payload.append({
                'title': task.assignment_title,
                'day': task.due_date.day,
                'month': task.due_date.month,
                'year': task.due_date.year,
                'is_exam': task.is_final_exam,
                'course': task.course.title if task.course else task.subject_tag,
            })

        context.update({
            'calendar_weeks': cal,
            'month_name': month_name,
            'year': year,
            'month': month,
            'today': today,
            'events_by_day': events_by_day,
            'deadlines_by_day': deadlines_by_day,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'upcoming_events': CalendarEvent.objects.filter(
                user=user, start_datetime__gte=timezone.now(),
            ).select_related('linked_course').order_by('start_datetime')[:12],
            'timetable_by_day': timetable_by_day,
            'weekday_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'enrolled_courses': enrolled_courses,
            'events_json': json.dumps(events_payload),
            'deadlines_json': json.dumps(deadlines_payload, default=str),
            'timetable_json': json.dumps([
                {
                    'id': s.id,
                    'weekday': s.weekday,
                    'title': s.title,
                    'start_time': s.start_time.strftime('%H:%M'),
                    'end_time': s.end_time.strftime('%H:%M'),
                    'slot_type': s.slot_type,
                    'color': s.color,
                    'course': s.course.title if s.course else '',
                    'notes': s.notes,
                }
                for s in timetable_slots
            ]),
            'event_type_colors': CALENDAR_EVENT_COLORS,
            'selected_day': int(self.request.GET.get('day', today.day if today.month == month and today.year == year else 0)),
        })
        return context

    def post(self, request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

        try:
            data = json.loads(request.body)
            action = data.get('action')
            user = request.user

            if action == 'create':
                event_type = data.get('event_type', 'reminder')
                start = _parse_event_datetime(data.get('start_datetime'))
                end = None
                if data.get('end_datetime'):
                    end = _parse_event_datetime(data.get('end_datetime'))
                course_id = data.get('linked_course_id')
                event = CalendarEvent.objects.create(
                    user=user,
                    title=data.get('title', 'New Event'),
                    description=data.get('description', ''),
                    event_type=event_type,
                    start_datetime=start,
                    end_datetime=end,
                    all_day=data.get('all_day', False),
                    color=data.get('color') or CALENDAR_EVENT_COLORS.get(event_type, '#E67E66'),
                    linked_course_id=course_id if course_id else None,
                )
                return JsonResponse({
                    'status': 'success',
                    'event_id': event.id,
                    'message': 'Event added to your calendar.',
                })

            if action == 'schedule_exam':
                course = None
                course_id = data.get('linked_course_id')
                if course_id:
                    course = Course.objects.filter(
                        pk=course_id, enrollments__user=user,
                    ).first()
                title = data.get('title') or (
                    f'{course.title} — Final Exam' if course else 'Scheduled Exam'
                )
                start = _parse_event_datetime(data.get('start_datetime'))
                duration = int(data.get('duration_minutes', 90))
                end = start + timedelta(minutes=duration)
                event = CalendarEvent.objects.create(
                    user=user,
                    title=title,
                    description=data.get('description', 'Scheduled exam session.'),
                    event_type='exam',
                    start_datetime=start,
                    end_datetime=end,
                    color=CALENDAR_EVENT_COLORS['exam'],
                    linked_course=course,
                )
                if course:
                    AssignmentTask.objects.filter(
                        user=user, course=course, is_final_exam=True,
                    ).update(due_date=start.date())
                return JsonResponse({
                    'status': 'success',
                    'event_id': event.id,
                    'message': 'Exam scheduled on your calendar.',
                })

            if action == 'delete':
                event = get_object_or_404(
                    CalendarEvent, id=data.get('event_id'), user=user,
                )
                event.delete()
                return JsonResponse({'status': 'success', 'message': 'Event removed.'})

            if action == 'create_timetable':
                course = None
                course_id = data.get('course_id')
                if course_id:
                    course = Course.objects.filter(
                        pk=course_id, enrollments__user=user,
                    ).first()
                slot = TimetableSlot.objects.create(
                    user=user,
                    weekday=int(data.get('weekday', 0)),
                    start_time=_parse_time_value(data.get('start_time')),
                    end_time=_parse_time_value(data.get('end_time', '10:00')),
                    title=data.get('title', 'Study block'),
                    slot_type=data.get('slot_type', 'custom'),
                    course=course,
                    notes=data.get('notes', ''),
                )
                return JsonResponse({
                    'status': 'success',
                    'slot_id': slot.id,
                    'message': 'Timetable updated.',
                })

            if action == 'update_timetable':
                slot = get_object_or_404(
                    TimetableSlot, id=data.get('slot_id'), user=user,
                )
                if 'weekday' in data:
                    slot.weekday = int(data['weekday'])
                if 'start_time' in data:
                    slot.start_time = _parse_time_value(data['start_time'])
                if 'end_time' in data:
                    slot.end_time = _parse_time_value(data['end_time'])
                if 'title' in data:
                    slot.title = data['title']
                if 'slot_type' in data:
                    slot.slot_type = data['slot_type']
                if 'notes' in data:
                    slot.notes = data['notes']
                if data.get('course_id'):
                    slot.course = Course.objects.filter(
                        pk=data['course_id'], enrollments__user=user,
                    ).first()
                slot.save()
                return JsonResponse({'status': 'success', 'message': 'Slot updated.'})

            if action == 'delete_timetable':
                slot = get_object_or_404(
                    TimetableSlot, id=data.get('slot_id'), user=user,
                )
                slot.delete()
                return JsonResponse({'status': 'success', 'message': 'Slot removed.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

        return JsonResponse({'status': 'error', 'message': 'Unknown action.'}, status=400)


# ── Coding game sandbox (Scratch / WoofJS) ────────────────────────────────────

@login_required
def game_sandbox_view(request, game_id):
    game = get_object_or_404(
        CodingGame.objects.select_related('module', 'module__course'),
        id=game_id,
    )
    return_url = reverse('games_library')
    if game.module_id:
        return_url = reverse('course_detail', kwargs={'slug': game.module.course.slug})
    return render(
        request,
        'dashboard/games_dashboard.html',
        {'game': game, 'return_url': return_url},
    )


# ── NEW: Games Library ────────────────────────────────────────────────────────

class GamesLibraryView(LoginRequiredMixin, TemplateView):
    template_name = 'games_library.html'

    def get_context_data(self, **kwargs):
        from core.subject_games import SUBJECT_GAME_LABS

        context = super().get_context_data(**kwargs)
        user = self.request.user

        category  = self.request.GET.get('category', 'all')
        age_group = self.request.GET.get('age', 'all')
        sandbox_type = self.request.GET.get('type', 'all')
        query = self.request.GET.get('q', '').strip()

        coding_games = CodingGame.objects.select_related(
            'module', 'module__course',
        ).order_by('module__course__title', 'module__order', 'title')
        if sandbox_type in ('scratch', 'woofjs'):
            coding_games = coding_games.filter(game_type=sandbox_type)
        if query:
            coding_games = coding_games.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(game_type__icontains=query) |
                Q(module__title__icontains=query) |
                Q(module__course__title__icontains=query)
            )

        module_sandboxes = coding_games.filter(module__isnull=False)
        standalone_sandboxes = coding_games.filter(module__isnull=True)

        games = EmbeddedGame.objects.filter(is_active=True)
        if category != 'all':
            games = games.filter(category=category)
        if age_group != 'all':
            games = games.filter(age_group=age_group)
        if query:
            games = games.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__icontains=query) |
                Q(age_group__icontains=query)
            )

        subject_labs = SUBJECT_GAME_LABS
        if category != 'all':
            subject_labs = [
                lab for lab in SUBJECT_GAME_LABS if lab.get('category') == category
            ]
        if age_group == '12-16':
            subject_labs = [
                lab for lab in subject_labs
                if '12-16' in lab.get('age_display', '')
            ]
        elif age_group not in ('all', '12-16'):
            subject_labs = []
        if query:
            normalized_query = query.lower()
            subject_labs = [
                lab for lab in subject_labs
                if normalized_query in lab.get('title', '').lower()
                or normalized_query in lab.get('description', '').lower()
                or normalized_query in lab.get('label', '').lower()
            ]

        context.update({
            'games':                games,
            'coding_games':         coding_games,
            'module_sandboxes':     module_sandboxes,
            'standalone_sandboxes': standalone_sandboxes,
            'active_sandbox_type':  sandbox_type,
            'subject_labs':         subject_labs,
            'featured_games': EmbeddedGame.objects.filter(is_active=True, is_featured=True)[:4],
            'categories':     ['all', 'math', 'science', 'language', 'coding', 'puzzle', 'geography'],
            'age_groups':     [('all', 'All Ages'), ('5-8', '5–8'), ('8-12', '8–12'), ('12-16', '12–16')],
            'active_cat':     category,
            'active_age':     age_group,
            'query':          query,
            'total_played':   GameSession.objects.filter(user=user).count(),
            'recently_played': GameSession.objects.filter(
                user=user
            ).select_related('game').order_by('-played_at')[:4],
        })
        return context

    def post(self, request, *args, **kwargs):
        """Log a game session when user launches a game."""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data    = json.loads(request.body)
                game_id = data.get('game_id')
                game    = get_object_or_404(EmbeddedGame, id=game_id, is_active=True)

                GameSession.objects.create(user=request.user, game=game)
                game.play_count += 1
                game.save(update_fields=['play_count'])

                return JsonResponse({
                    'status': 'success',
                    'embed_url': game.embed_url,
                    'title':     game.title,
                })
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
