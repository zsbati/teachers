from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.core.exceptions import PermissionDenied
from django.http import Http404

def teacher_or_superuser(function=None, login_url=None, redirect_field_name=None):
    """
    Decorator that ensures the user is either a superuser or the teacher themselves.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser or (hasattr(u, 'teacher') and u.is_authenticated),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

from .forms import (
    CustomPasswordChangeForm, TeacherCreationForm, TaskForm,
    WorkSessionManualForm, WorkSessionClockForm, WorkSessionTimeRangeForm, WorkSessionFilterForm, AddTeacherForm,
    ChangeTeacherPasswordForm, SalaryReportForm, StudentCreationForm, EditStudentForm, ChangeStudentPasswordForm
)
from .models import Teacher, CustomUser, Task, WorkSession, SalaryReport, Student

@login_required
@user_passes_test(lambda u: u.is_superuser)
def view_deactivated_students(request):
    deactivated_students = Student.objects.filter(is_active=False)
    context = {
        'deactivated_students': deactivated_students
    }
    return render(request, 'superuser/view_deactivated_students.html', context)

from .services import SalaryCalculationService


def is_superuser(user):
    return user.is_superuser


def is_teacher(user):
    return user.is_teacher


@login_required
def dashboard_redirect(request):
    """
    Redirects the user to the appropriate dashboard based on their role.
    """
    if request.user.is_superuser:
        return redirect('superuser_dashboard')
    elif hasattr(request.user, 'is_student') and request.user.is_student:
        return redirect('student_dashboard')
    elif request.user.is_teacher:
        return redirect('teachers_dashboard')
    else:
        return redirect('dashboard_login')


@login_required
def teachers_dashboard(request):
    """
    View for the teacher's dashboard.
    """
    return render(request, 'teachers/dashboard.html')


@login_required
def student_dashboard(request):
    """
    View for the student's dashboard.
    """
    return render(request, 'student/dashboard.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def superuser_dashboard(request):
    """
    View for the superuser's dashboard.
    """
    return render(request, 'superuser/dashboard.html')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'change_password.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_teachers(request):
    if request.method == "POST":
        form = AddTeacherForm(request.POST)
        if form.is_valid():
            # Create user
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                is_teacher=True
            )
            # Create teacher
            Teacher.objects.create(
                user=user,
                subjects=form.cleaned_data['subjects']
            )
            messages.success(request, f'Teacher {user.username} was successfully added!')
            return redirect('manage_teachers')
        else:
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)  # Debug: Print form errors
    else:
        form = AddTeacherForm()

    teachers = Teacher.objects.all()
    print(f"Teachers in view: {teachers}")  # Debug: Print teachers in the view

    context = {
        'form': form,
        'teachers': teachers,
    }
    return render(request, 'superuser/manage_teachers.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_students(request):
    active_students = Student.objects.filter(is_active=True)
    deactivated_students = Student.objects.filter(is_active=False)
    form = StudentCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        messages.success(request, f'Student {user.username} created successfully.')
        return redirect('manage_students')
    
    context = {
        'form': form,
        'active_students': active_students,
        'deactivated_students': deactivated_students
    }
    return render(request, 'superuser/manage_students.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == "POST":
        form = EditStudentForm(request.POST, instance=student)
        if form.is_valid():
            # Save the student profile
            student = form.save(commit=False)
            # Update the user's email if it changed
            try:
                if 'email' in form.cleaned_data and form.cleaned_data['email'] != student.user.email:
                    student.user.email = form.cleaned_data['email']
                    student.user.save()
            except CustomUser.DoesNotExist:
                pass  # No user associated, skip email update
            student.save()
            messages.success(request, f'Student {student.user.username} updated successfully.')
            return redirect('manage_students')
    else:
        # Initialize form with current values
        initial_data = {
            'phone': student.phone,
            'is_active': student.is_active,
            'email': getattr(student.user, 'email', '')
        }
        form = EditStudentForm(initial=initial_data)
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'superuser/edit_student.html', context)


@login_required
def edit_own_profile(request):
    """Student view to edit their own profile."""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'You do not have a student profile.')
        return redirect('student_dashboard')
    
    if request.method == "POST":
        form = EditStudentForm(request.POST, instance=student)
        if form.is_valid():
            # Save the student profile
            student = form.save(commit=False)
            # Update the user's email if it changed
            try:
                if 'email' in form.cleaned_data and form.cleaned_data['email'] != student.user.email:
                    student.user.email = form.cleaned_data['email']
                    student.user.save()
            except CustomUser.DoesNotExist:
                pass  # No user associated, skip email update
            student.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('student_dashboard')
    else:
        # Initialize form with current values
        initial_data = {
            'phone': student.phone,
            'is_active': student.is_active,
            'email': getattr(student.user, 'email', '')
        }
        form = EditStudentForm(initial=initial_data)
    
    context = {
        'form': form,
        'student': student,
        'is_own_profile': True
    }
    return render(request, 'student/edit_profile.html', context)
    student = get_object_or_404(Student, id=student_id)
    if request.method == "POST":
        form = EditStudentForm(request.POST, instance=student)
        if form.is_valid():
            # Save the student profile
            student = form.save(commit=False)
            # Update the user's email if it changed
            try:
                if 'email' in form.cleaned_data and form.cleaned_data['email'] != student.user.email:
                    student.user.email = form.cleaned_data['email']
                    student.user.save()
            except CustomUser.DoesNotExist:
                pass  # No user associated, skip email update
            student.save()
            messages.success(request, f'Student {student.user.username} updated successfully.')
            return redirect('manage_students')
    else:
        # Initialize form with current values
        initial_data = {
            'phone': student.phone,
            'is_active': student.is_active,
            'email': getattr(student.user, 'email', '')
        }
        form = EditStudentForm(initial=initial_data)
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'superuser/edit_student.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def remove_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        # Deactivate the student profile instead of deleting
        student.is_active = False
        student.save()
        messages.success(request, f'Student {student.user.username} deactivated successfully.')
        return redirect('manage_students')
    # GET: render confirmation page
    return render(request, 'superuser/confirm_student_removal.html', {'student': student})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reactivate_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.is_active = True
        student.save()
        messages.success(request, f'Student {student.user.username} reactivated successfully.')
        return redirect('manage_students')
    # GET: render confirmation page
    return render(request, 'superuser/confirm_student_reactivation.html', {'student': student})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        username = student.user.username
        student.user.delete()  # This will cascade delete the Student profile as well
        messages.success(request, f'Student {username} permanently deleted.')
        return redirect('view_deactivated_students')
    # GET: render confirmation page
    return render(request, 'superuser/confirm_student_delete.html', {'student': student})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def change_student_password(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = ChangeStudentPasswordForm(request.POST)
        if form.is_valid():
            form.save(student.user)
            messages.success(request, f'Password for {student.user.username} has been changed successfully.')
            return redirect('manage_students')
    else:
        form = ChangeStudentPasswordForm()
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'superuser/change_student_password.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_work_sessions(request):
    work_sessions = WorkSession.objects.select_related('task', 'teacher').order_by('-start_time')
    context = {
        'work_sessions': work_sessions
    }
    return render(request, 'superuser/list_work_sessions.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_work_session(request, session_id):
    session = get_object_or_404(WorkSession, id=session_id)
    
    # Determine which form to use based on the existing session type
    if session.entry_type == 'manual':
        FormClass = WorkSessionManualForm
    elif session.entry_type == 'clock':
        FormClass = WorkSessionClockForm
    else:  # time_range
        FormClass = WorkSessionTimeRangeForm
    
    if request.method == "POST":
        form = FormClass(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Work session updated successfully.')
            return redirect('superuser_list_work_sessions')
    else:
        form = FormClass(instance=session)
    
    context = {
        'form': form,
        'session': session
    }
    return render(request, 'superuser/edit_work_session.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_work_session(request, session_id):
    session = get_object_or_404(WorkSession, id=session_id)
    if request.method == "POST":
        session.delete()
        messages.success(request, 'Work session deleted successfully.')
        return redirect('superuser_list_work_sessions')
    
    context = {
        'session': session
    }
    return render(request, 'superuser/confirm_work_session_deletion.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_tasks(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.name}" was successfully added!')
            return redirect('manage_tasks')
        else:
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)  # Debugging
    else:
        form = TaskForm()

    tasks = Task.objects.all()
    print(f"Tasks in view: {tasks}")  # Debugging

    context = {
        'form': form,
        'tasks': tasks,
    }
    return render(request, 'superuser/manage_tasks.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_teacher(request):
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            # Create user
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],  # Retrieve email from the form
                password=form.cleaned_data['password'],
                is_teacher=True
            )
            # Create teacher
            Teacher.objects.create(
                user=user,
                subjects=form.cleaned_data['subjects']
            )
            messages.success(request, f'Teacher {user.username} was successfully added!')
            return redirect('manage_teachers')
    else:
        form = TeacherCreationForm()

    teachers = Teacher.objects.all()
    return render(request, 'superuser/manage_teachers.html', {'form': form, 'teachers': teachers})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def remove_teacher(request, teacher_id):
    try:
        teacher = Teacher.objects.get(id=teacher_id)
        # Delete the associated user first (this will cascade delete the teacher)
        teacher.user.delete()
        messages.success(request, f'Teacher {teacher.user.username} has been successfully removed.')
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher not found.')
    except Exception as e:
        messages.error(request, f'Error removing teacher: {str(e)}')

    return redirect('manage_teachers')


@login_required
@user_passes_test(is_superuser)
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task was successfully updated!')
            return redirect('manage_tasks')
    else:
        form = TaskForm(instance=task)

    return render(request, 'edit_task.html', {
        'form': form,
        'task': task
    })


@login_required
@user_passes_test(is_superuser)
def remove_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task was successfully removed!')
        return redirect('manage_tasks')
    return render(request, 'superuser/confirm_task_removal.html', {'task': task})


@login_required
def record_work(request, teacher_id=None):
    # Determine the teacher for whom the work is being recorded
    if not request.user.is_superuser:
        teacher = get_object_or_404(Teacher, user=request.user)  # Teachers can only record their own work
    else:
        if teacher_id:
            teacher = get_object_or_404(Teacher, id=teacher_id)  # Superusers specify a teacher
        else:
            return HttpResponseForbidden("Superusers must specify a teacher to record work for.")

    if request.method == 'POST':
        entry_type = request.POST.get('entry_type')

        if entry_type == 'manual':
            form = WorkSessionManualForm(request.POST)
            if form.is_valid():
                work_session = form.save(commit=False)
                work_session.teacher = teacher
                work_session.entry_type = 'manual'
                work_session.save()
                messages.success(request, f'Work hours recorded successfully for {teacher.user.username}!')
                return redirect('record_work_with_teacher', teacher_id=teacher.id)

        elif entry_type == 'clock':
            form = WorkSessionClockForm(request.POST)
            if form.is_valid():
                work_session = form.save(commit=False)
                work_session.teacher = teacher
                work_session.entry_type = 'clock'
                work_session.clock_in = timezone.now()
                work_session.save()
                messages.success(request, f'Clock-in recorded successfully for {teacher.user.username}!')
                return redirect('record_work_with_teacher', teacher_id=teacher.id)

        elif entry_type == 'time_range':
            form = WorkSessionTimeRangeForm(request.POST)
            if form.is_valid():
                work_session = form.save(commit=False)
                work_session.teacher = teacher
                work_session.entry_type = 'time_range'
                work_session.save()
                messages.success(request,
                                 f'Work hours recorded successfully with a time range for {teacher.user.username}!')
                return redirect('record_work_with_teacher', teacher_id=teacher.id)

    else:
        manual_form = WorkSessionManualForm()
        clock_form = WorkSessionClockForm()
        time_range_form = WorkSessionTimeRangeForm()

    # Get the active session for the teacher
    active_session = WorkSession.objects.filter(
        teacher=teacher,
        entry_type='clock',
        clock_out__isnull=True
    ).first()

    # Get completed sessions for the teacher
    completed_sessions = WorkSession.objects.filter(
        teacher=teacher
    ).exclude(
        id=active_session.id if active_session else None
    ).order_by('-created_at')[:10]

    return render(request, 'record_work.html', {
        'manual_form': manual_form,
        'clock_form': clock_form,
        'time_range_form': time_range_form,
        'active_session': active_session,
        'completed_sessions': completed_sessions,
        'teacher': teacher,
    })


@login_required
@user_passes_test(is_teacher)
def clock_out(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(
            WorkSession,
            id=session_id,
            teacher=request.user.teacher,
            entry_type='clock',
            clock_out__isnull=True
        )
        session.clock_out = timezone.now()
        session.save()
        messages.success(request, 'Clocked out successfully!')
    return redirect('record_work')


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_teacher)  # Allow both roles to access
def recent_work_sessions(request, teacher_id=None):
    # Check if the user is a teacher or a superuser
    if not request.user.is_superuser:
        # For teachers, get their own teacher instance
        teacher = get_object_or_404(Teacher, user=request.user)
    else:
        # For superusers, get the teacher by ID
        teacher = get_object_or_404(Teacher, id=teacher_id)

    # Fetch recent work sessions for the teacher
    work_sessions = WorkSession.objects.filter(teacher=teacher).order_by('-created_at')[:10]

    # Debugging: Print the teacher and work sessions to the console
    print(f"Teacher: {teacher}")
    print(f"Work Sessions: {work_sessions}")

    context = {
        'teacher': teacher,
        'work_sessions': work_sessions,
    }
    return render(request, 'recent_work_sessions.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def change_teacher_password(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'POST':
        form = ChangeTeacherPasswordForm(request.POST)
        if form.is_valid():
            teacher.user.set_password(form.cleaned_data['new_password'])
            teacher.user.save()
            messages.success(request, f'Password for {teacher.user.username} has been changed successfully!')
            return redirect('manage_teachers')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChangeTeacherPasswordForm()

    return render(request, 'superuser/change_teacher_password.html', {
        'form': form,
        'teacher': teacher
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_salary_report(request):
    if request.method == 'POST':
        form = SalaryReportForm(request.POST)
        if form.is_valid():
            teacher = form.cleaned_data['teacher']
            year = form.cleaned_data['year']
            month = int(form.cleaned_data['month'])
            notes = form.cleaned_data['notes']

            # Create start and end dates for the month
            start_date = timezone.datetime(year, month, 1)
            if month == 12:
                end_date = timezone.datetime(year + 1, 1, 1)
            else:
                end_date = timezone.datetime(year, month + 1, 1)
            end_date = end_date - timezone.timedelta(microseconds=1)

            # Check if a report exists for this period
            existing_reports = SalaryReport.objects.filter(
                teacher=teacher,
                start_date=start_date,
                end_date=end_date
            )
            
            if existing_reports.exists():
                # Delete any existing reports for this period
                existing_reports.delete()
            
            # Create a new report
            report = SalaryReport.objects.create(
                teacher=teacher,
                start_date=start_date,
                end_date=end_date,
                created_by=request.user,
                notes=notes
            )

            # Calculate salary details
            report_data = SalaryCalculationService.calculate_salary(teacher, year, month)
            
            # Since we're always creating a new report, we don't need to check if it was created
            message = f'Salary report created for {teacher.user.username} - {report_data["period"]}'
            messages.success(request, message)
            
            return redirect('view_salary_report', teacher_id=teacher.id, year=year, month=month)
    else:
        form = SalaryReportForm()

    return render(request, 'superuser/create_salary_report.html', {
        'form': form
    })


@login_required
@teacher_or_superuser
def view_salary_report(request, teacher_id, year, month):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Get the report for this month
    start_date = timezone.datetime(year, month, 1)
    if month == 12:
        end_date = timezone.datetime(year + 1, 1, 1)
    else:
        end_date = timezone.datetime(year, month + 1, 1)
    end_date = end_date - timezone.timedelta(microseconds=1)
    
    # Get the report for this period
    reports = SalaryReport.objects.filter(
        teacher=teacher,
        start_date=start_date,
        end_date=end_date,
        is_deleted=False
    ).order_by('-created_at')
    
    if not reports.exists():
        # If no report exists, create a new one
        report = SalaryReport.objects.create(
            teacher=teacher,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user
        )
    else:
        # If a report exists, use it
        report = reports.first()

    # Calculate the report data - FIXED: Use static method
    report_data = SalaryCalculationService.calculate_salary(teacher, year, month)

    # Check permissions
    if request.user.is_superuser:
        template = 'superuser/view_salary_report.html'
    elif request.user == teacher.user:
        template = 'teachers/view_salary_report.html'
    else:
        raise PermissionDenied("You do not have permission to view this report")

    return render(request, template, {
        'teacher': teacher,
        'report': report,
        'report_data': report_data
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_salary_reports(request, teacher_id=None):
    if teacher_id:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        reports = SalaryReport.objects.filter(
            teacher=teacher,
            is_deleted=False
        ).order_by('-start_date')
    else:
        teacher = None
        reports = SalaryReport.objects.filter(
            is_deleted=False
        ).order_by('-start_date')

    # For each report, calculate the salary - FIXED: Use static method
    reports_with_data = []
    for report in reports:
        year = report.start_date.year
        month = report.start_date.month
        report_data = SalaryCalculationService.calculate_salary(report.teacher, year, month)
        reports_with_data.append({
            'report': report,
            'total_salary': report_data['total_salary']
        })

    return render(request, 'superuser/list_salary_reports.html', {
        'teacher': teacher,
        'reports': reports_with_data
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_salary_report(request, report_id):
    """Delete a salary report and redirect back to the list."""
    report = get_object_or_404(SalaryReport, id=report_id)
    report.delete()
    messages.success(request, 'Salary report deleted successfully.')
    return redirect('list_salary_reports')


@login_required
@user_passes_test(lambda u: u.is_teacher)
def teacher_salary_reports(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    reports = SalaryReport.objects.filter(teacher=teacher).order_by('-start_date')

    # For each report, calculate the salary (reuse logic)
    reports_with_data = []
    for report in reports:
        year = report.start_date.year
        month = report.start_date.month
        report_data = SalaryCalculationService.calculate_salary(report.teacher, year, month)
        reports_with_data.append({
            'report': report,
            'total_salary': report_data['total_salary']
        })

    return render(request, 'teachers/teacher_salary_reports.html', {
        'reports': reports_with_data
    })