from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, billing_views, salary_views
from .service_views import manage_services, add_service, edit_service, delete_service

urlpatterns = [
    path('superuser/manage-services/', manage_services, name='manage_services'),
    path('superuser/add-service/', add_service, name='add_service'),
    path('superuser/edit-service/<int:service_id>/', edit_service, name='edit_service'),
    path('superuser/delete-service/<int:service_id>/', delete_service, name='delete_service'),
    path('dashboard/superuser/work-sessions/', views.list_work_sessions, name='superuser_list_work_sessions'),
    path('dashboard/superuser/work-sessions/<int:session_id>/edit/', views.edit_work_session, name='edit_work_session'),
    path('dashboard/superuser/work-sessions/<int:session_id>/delete/', views.delete_work_session, name='delete_work_session'),
    path('dashboard/superuser/edit-student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('', views.dashboard_redirect, name='dashboard'),  # Root path now uses dynamic redirect
    path('dashboard/teachers/', views.teachers_dashboard, name='teachers_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/student/edit-profile/', views.edit_own_profile, name='edit_own_profile'),
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
    path('dashboard/student/<int:student_id>/bills/create/', billing_views.create_bill_final, name='create_bill'),

    # Salary Report URLs
    path('superuser/salary-reports/', views.list_salary_reports, name='list_salary_reports'),
    path('superuser/salary-reports/<int:teacher_id>/', views.list_salary_reports, name='list_salary_reports'),
    path('superuser/salary-reports/create/', salary_views.create_salary_report, name='create_salary_report'),
    path('superuser/salary-reports/<int:teacher_id>/<int:year>/<int:month>/', views.view_salary_report,
         name='view_salary_report'),
    path('superuser/salary-reports/<int:report_id>/delete/', views.delete_salary_report, name='delete_salary_report'),
    path('dashboard/teacher/salary-reports/', views.teacher_salary_reports, name='teacher_salary_reports'),
    path('dashboard/teacher/salary-reports/<int:teacher_id>/<int:year>/<int:month>/', views.view_salary_report, name='teacher_view_salary_report'),

    # Bulk Salary Reports for All Teachers
    path('dashboard/superuser/salary-reports-bulk/', salary_views.salary_reports_bulk, name='salary_reports_bulk'),

    # Billing URLs
    path('superuser/billing/', billing_views.select_student_for_billing, name='select_student_billing'),
    path('superuser/create-bill/', billing_views.select_student_for_bill_creation, name='select_student_for_bill_creation'),
    path('superuser/bill-all-students/', billing_views.bill_all_students, name='bill_all_students'),
    path('student/<int:student_id>/bills/', billing_views.student_bills, name='student_bills'),
    path('student/<int:student_id>/bills/create/', billing_views.create_bill, name='create_bill'),
    path('bill/<int:bill_id>/', billing_views.bill_detail, name='bill_detail'),
    path('dashboard/superuser/charge-student-for-service/', billing_views.charge_student_for_service, name='charge_student_for_service'),
    path('superuser/student/<int:student_id>/bill-items/', billing_views.student_bill_items, name='student_bill_items'),
    path('bill-item/<int:item_id>/edit/', billing_views.edit_bill_item, name='edit_bill_item'),
    path('bill-item/<int:item_id>/delete/', billing_views.delete_bill_item, name='delete_bill_item'),

    path('manage-inspectors/', views.manage_inspectors, name='manage_inspectors'),
    path('delete-inspector/<int:inspector_id>/', views.delete_inspector, name='delete_inspector'),
    path('change-inspector-password/<int:inspector_id>/', views.change_inspector_password, name='change_inspector_password'),
]
