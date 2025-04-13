from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # Da
    path('dashboard/', views.dashboard, name='dashboard'),
    path('change-password/', views.change_password, name='change_password'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='registration/logged_out.html',
        next_page='login'
    ), name='logout'),
    path('manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('add-teacher/', views.add_teacher, name='add_teacher'),
    path('remove-teacher/<int:teacher_id>/', views.remove_teacher, name='remove_teacher'),
    path('manage-tasks/', views.manage_tasks, name='manage_tasks'),
    path('edit-task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('remove-task/<int:task_id>/', views.remove_task, name='remove_task'),
    path('record-work/', views.record_work, name='record_work'),
    path('clock-out/<int:session_id>/', views.clock_out, name='clock_out'),
    path('recent-work-sessions/', views.recent_work_sessions, name='recent_work_sessions'),
]
