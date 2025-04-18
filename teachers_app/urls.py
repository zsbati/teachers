from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('dashboard/superuser/work-sessions/', views.list_work_sessions, name='superuser_list_work_sessions'),
    path('dashboard/superuser/work-sessions/<int:session_id>/edit/', views.edit_work_session, name='edit_work_session'),
    path('dashboard/superuser/work-sessions/<int:session_id>/delete/', views.delete_work_session, name='delete_work_session'),
    path('dashboard/superuser/edit-student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('', views.dashboard_redirect, name='dashboard'),  # Root path now uses dynamic redirect
    path('dashboard/teachers/', views.teachers_dashboard, name='teachers_dashboard'),
    path('dashboard/superuser/', views.superuser_dashboard, name='superuser_dashboard'),
    path('change-password/', views.change_password, name='change_password'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='registration/logged_out.html',
        next_page='login'
    ), name='logout'),
    path('superuser/manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('superuser/remove-teacher/<int:teacher_id>/', views.remove_teacher, name='remove_teacher'),
    path('superuser/change-teacher-password/<int:teacher_id>/', views.change_teacher_password,
         name='change_teacher_password'),
    path('add-teacher/', views.add_teacher, name='add_teacher'),
    path('superuser/manage-tasks/', views.manage_tasks, name='manage_tasks'),
    path('edit-task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('remove-task/<int:task_id>/', views.remove_task, name='remove_task'),
    path('superuser/manage-students/', views.manage_students, name='manage_students'),
    path('remove-student/<int:student_id>/', views.remove_student, name='remove_student'),
    path('reactivate-student/<int:student_id>/', views.reactivate_student, name='reactivate_student'),
    path('superuser/deactivated-students/', views.view_deactivated_students, name='view_deactivated_students'),
    path('delete-student/<int:student_id>/', views.delete_student, name='delete_student'),
    path('change-student-password/<int:student_id>/', views.change_student_password, name='change_student_password'),
    path('record-work/', views.record_work, name='record_work'),  # For teachers recording their own work
    path('record-work/<int:teacher_id>/', views.record_work, name='record_work_with_teacher'),
    path('clock-out/<int:session_id>/', views.clock_out, name='clock_out'),
    path('dashboard/recent-work-sessions/<int:teacher_id>/', views.recent_work_sessions, name='recent_work_sessions'),

    # Salary Report URLs
    path('superuser/salary-reports/', views.list_salary_reports, name='list_salary_reports'),
    path('superuser/salary-reports/<int:teacher_id>/', views.list_salary_reports, name='list_salary_reports'),
    path('superuser/salary-reports/create/', views.create_salary_report, name='create_salary_report'),
    path('superuser/salary-reports/<int:teacher_id>/<int:year>/<int:month>/', views.view_salary_report,
         name='view_salary_report'),
    path('superuser/salary-reports/<int:report_id>/delete/', views.delete_salary_report, name='delete_salary_report'),
    path('dashboard/teacher/salary-reports/', views.teacher_salary_reports, name='teacher_salary_reports'),
]
