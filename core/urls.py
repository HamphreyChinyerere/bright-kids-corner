from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    DashboardMapView,
    GlobalSearchView,
    CourseListView,
    CourseDetailView,
    LessonDetailView,
    ProjectsHubListView,
    AssignmentWorkspaceView,
    CertificationsView,
    RewardsVaultView,
    CertificatePDFExportView,
    VRHardwareControllerView,
    VRSpaceSimulationView,
    VR360VideoView,
    VRWebXRView,
    VRComingSoonView,
    AuthView,
    HomeRedirectView,
    check_username_exists,
    toggle_view_density,
    ProfileHubView,
    KidsModeView,
    CalendarView,
    GamesLibraryView,
    game_sandbox_view,
)

urlpatterns = [
    # ── Core ──────────────────────────────────────────────────────────────────
    path('', HomeRedirectView.as_view(), name='home'),
    path('auth/', AuthView.as_view(), name='auth'),
    path('api/check-username/', check_username_exists, name='check_username'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/auth/?mode=login'), name='logout'),
    path('toggle-view/', toggle_view_density, name='toggle_view'),

    # ── Main Pages ─────────────────────────────────────────────────────────────
    path('dashboard/', DashboardMapView.as_view(), name='dashboard'),
    path('search/', GlobalSearchView.as_view(), name='global_search'),
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('courses/<slug:slug>/', CourseDetailView.as_view(), name='course_detail'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson_detail'),
    path('projects/', ProjectsHubListView.as_view(), name='projects_hub'),
    path('assignments/', AssignmentWorkspaceView.as_view(), name='assignment_workspace'),
    path('certifications/', CertificationsView.as_view(), name='certifications'),
    path('rewards/', RewardsVaultView.as_view(), name='rewards_vault'),
    path('rewards/export/<uuid:token>/', CertificatePDFExportView.as_view(), name='certificate_export'),
    path('profile/', ProfileHubView.as_view(), name='profile_hub'),    path('kids-mode/', KidsModeView.as_view(), name='kids_mode'),
    # ── Calendar ───────────────────────────────────────────────────────────────
    path('calendar/', CalendarView.as_view(), name='calendar'),

    # ── Games ──────────────────────────────────────────────────────────────────
    path('games/', GamesLibraryView.as_view(), name='games_library'),
    path('games/sandbox/<int:game_id>/', game_sandbox_view, name='game_sandbox'),

    # ── VR Portal (sub-sections) ───────────────────────────────────────────────
    path('vr/', VRHardwareControllerView.as_view(), name='vr_portal'),
    path('vr/360/', VR360VideoView.as_view(), name='vr_360'),
    path('vr/webxr/', VRWebXRView.as_view(), name='vr_webxr'),
    path('vr/coming-soon/', VRComingSoonView.as_view(), name='vr_coming_soon'),
    path('vr/simulation/', VRSpaceSimulationView.as_view(), name='vr_simulation'),
]
