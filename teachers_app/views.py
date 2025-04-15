from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseForbidden
from .forms import (
    CustomPasswordChangeForm, TeacherCreationForm, TaskForm,
    WorkSessionManualForm, WorkSessionClockForm, WorkSessionTimeRangeForm, WorkSessionFilterForm, AddTeacherForm,
    ChangeTeacherPasswordForm, SalaryReportForm
)
from .models import Teacher, CustomUser, Task, WorkSession, SalaryReport
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
    else:
        return redirect('teachers_dashboard')


@login_required
def teachers_dashboard(request):
    """
    View for the teacher's dashboard.
    """
    return render(request, 'teachers/dashboard.html')


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
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        task.delete()
        messages.success(request, 'Task was successfully removed!')
    return redirect('manage_tasks')


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

            # Create the report
            report = SalaryReport.objects.create(
                teacher=teacher,
                start_date=start_date,
                end_date=end_date,
                created_by=request.user,
                notes=notes
            )

            # Calculate salary details - FIXED: Use static method
            report_data = SalaryCalculationService.calculate_salary(teacher, year, month)

            messages.success(request, f'Salary report created for {teacher.user.username} - {report_data["period"]}')
            return redirect('view_salary_report', teacher_id=teacher.id, year=year, month=month)
    else:
        form = SalaryReportForm()

    return render(request, 'superuser/create_salary_report.html', {
        'form': form
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def view_salary_report(request, teacher_id, year, month):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    # Get the report for this month
    start_date = timezone.datetime(year, month, 1)
    if month == 12:
        end_date = timezone.datetime(year + 1, 1, 1)
    else:
        end_date = timezone.datetime(year, month + 1, 1)
    end_date = end_date - timezone.timedelta(microseconds=1)

    report = get_object_or_404(SalaryReport,
                               teacher=teacher,
                               start_date=start_date,
                               end_date=end_date)

    # Calculate the report data - FIXED: Use static method
    report_data = SalaryCalculationService.calculate_salary(teacher, year, month)

    return render(request, 'superuser/view_salary_report.html', {
        'teacher': teacher,
        'report': report,
        'report_data': report_data
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_salary_reports(request, teacher_id=None):
    if teacher_id:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        reports = SalaryReport.objects.filter(teacher=teacher).order_by('-start_date')
    else:
        teacher = None
        reports = SalaryReport.objects.all().order_by('-start_date')

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
