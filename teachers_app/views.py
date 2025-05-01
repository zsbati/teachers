from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseForbidden

# Import models from models.py
from .models import Task, WorkSession, Teacher, Student, CustomUser, SalaryReport, Inspector

# Import billing models from billing_models.py
from .billing_models import Bill, BillItem

# Import views from billing_views.py
from .billing_views import create_bill, student_bills, bill_detail

from .forms import (
    CustomPasswordChangeForm, TeacherCreationForm, TaskForm,
    WorkSessionManualForm, WorkSessionClockForm, WorkSessionTimeRangeForm, WorkSessionFilterForm, AddTeacherForm,
    ChangeTeacherPasswordForm, SalaryReportForm, StudentCreationForm, EditStudentForm, ChangeStudentPasswordForm,
    InspectorCreationForm
)
from .services import SalaryCalculationService


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


def is_inspector(function=None, login_url=None, redirect_field_name=None):
    """
    Decorator that ensures the user is either a superuser or an inspector.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser or u.is_inspector,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def is_inspector_effective(user):
    """
    Returns True if user is either a superuser or an inspector.
    """
    return user.is_superuser or user.is_inspector

def is_superuser(user):
    return user.is_superuser


def is_teacher(user):
    return user.is_teacher


@login_required
def dashboard_redirect(request):
    """
    Redirects the user to the appropriate dashboard based on their role.
    """
    if request.user.is_inspector:
        return redirect('superuser_dashboard')
    elif getattr(request.user, 'is_student', False):
        return redirect('student_dashboard')
    elif getattr(request.user, 'is_teacher', False):
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
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def superuser_dashboard(request):
    """
    Dashboard for both superuser and inspector roles.
    Inspectors see all info but cannot edit/add/delete.
    """
    can_edit = request.user.is_superuser
    return render(request, 'superuser/dashboard.html', {'can_edit': can_edit})


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
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def manage_teachers(request):
    teachers = Teacher.objects.all()
    can_edit = request.user.is_superuser
    if request.method == "POST" and can_edit:
        form = AddTeacherForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            # Check for lingering CustomUser before creation
            from .models import CustomUser
            lingering_user = CustomUser.objects.filter(username=username).first()
            if lingering_user:
                try:
                    lingering_user.delete()
                    messages.warning(request, f"Lingering user '{username}' found and deleted before re-adding.")
                except Exception as e:
                    messages.error(request, f"Failed to delete lingering user '{username}': {e}")
                    return redirect('manage_teachers')
            # Now create user and teacher
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=form.cleaned_data['password'],
                is_teacher=True
            )
            Teacher.objects.create(
                user=user,
                subjects=form.cleaned_data['subjects']
            )
            messages.success(request, f'Teacher {user.username} was successfully added!')
            return redirect('manage_teachers')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddTeacherForm()
    context = {
        'form': form,
        'teachers': teachers,
        'can_edit': can_edit,
    }
    return render(request, 'superuser/manage_teachers.html', context)


@login_required
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def manage_students(request):
    active_students = Student.objects.filter(is_active=True)
    deactivated_students = Student.objects.filter(is_active=False)
    can_add = request.user.is_superuser
    form = StudentCreationForm(request.POST or None)
    if form.is_valid() and can_add:
        user = form.save()
        # Set user as student
        user.is_student = True
        user.save()
        # Create Student profile
        Student.objects.create(
            user=user,
            phone=form.cleaned_data.get('phone', ''),
            is_active=form.cleaned_data.get('is_active', True)
        )
        messages.success(request, f'Student {user.username} created successfully.')
        return redirect('manage_students')
    context = {
        'form': form,
        'active_students': active_students,
        'deactivated_students': deactivated_students,
        'can_add': can_add,
    }
    return render(request, 'superuser/manage_students.html', context)


@login_required
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def manage_tasks(request):
    can_edit = request.user.is_superuser
    if request.method == "POST" and can_edit:
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
        'can_edit': can_edit,
    }
    return render(request, 'superuser/manage_tasks.html', context)


@login_required
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def manage_inspectors(request):
    from .models import Inspector, CustomUser
    from .forms import InspectorCreationForm
    inspectors = Inspector.objects.select_related('user').all()
    can_edit = request.user.is_superuser
    form = InspectorCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid() and can_edit:
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        # Create user
        user = CustomUser.objects.create_user(username=username, email=email, password=password, is_inspector=True)
        Inspector.objects.create(user=user)
        messages.success(request, f'Inspector {username} created successfully.')
        return redirect('manage_inspectors')
    return render(request, 'superuser/manage_inspectors.html', {'form': form, 'inspectors': inspectors, 'can_edit': can_edit})


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
        return redirect('manage_students')
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
    student_id = session.student_id
    if request.method == "POST":
        session.delete()
        messages.success(request, 'Work session deleted successfully.')
        return redirect('student_bill_items', student_id=student_id)
    
    context = {
        'session': session
    }
    return render(request, 'superuser/confirm_work_session_deletion.html', context)

@login_required
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def manage_tasks(request):
    can_edit = request.user.is_superuser
    if request.method == "POST" and can_edit:
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
        'can_edit': can_edit,
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
    import logging
    logger = logging.getLogger(__name__)
    try:
        teacher = Teacher.objects.get(id=teacher_id)
        user = teacher.user
        teacher.delete()
        try:
            user.delete()
            messages.success(request, f'Teacher {user.username} has been successfully removed.')
        except Exception as ue:
            logger.error(f"Error deleting user instance for teacher {teacher_id}: {ue}")
            messages.error(request, f'Error deleting user instance: {ue}')
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher not found.')
    except Exception as e:
        logger.error(f"Error removing teacher: {e}")
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

    # Always define all forms
    manual_form = WorkSessionManualForm()
    clock_form = WorkSessionClockForm()
    time_range_form = WorkSessionTimeRangeForm()

    if request.method == 'POST':
        entry_type = request.POST.get('entry_type')

        if entry_type == 'manual':
            manual_form = WorkSessionManualForm(request.POST)
            if manual_form.is_valid():
                work_session = manual_form.save(commit=False)
                work_session.teacher = teacher
                work_session.entry_type = 'manual'
                work_session.save()
                from .billing_services import StudentBillingService
                if work_session.student:
                    StudentBillingService.create_bill_item_for_work_session(work_session)
                messages.success(request, f'Work hours recorded successfully for {teacher.user.username}!')
                return redirect('record_work_with_teacher', teacher_id=teacher.id)
        elif entry_type == 'clock':
            clock_form = WorkSessionClockForm(request.POST)
            if clock_form.is_valid():
                work_session = clock_form.save(commit=False)
                work_session.teacher = teacher
                work_session.entry_type = 'clock'
                work_session.clock_in = timezone.now()
                work_session.save()
                from .billing_services import StudentBillingService
                if work_session.student:
                    StudentBillingService.create_bill_item_for_work_session(work_session)
                messages.success(request, f'Clock-in recorded successfully for {teacher.user.username}!')
                return redirect('record_work_with_teacher', teacher_id=teacher.id)
        elif entry_type == 'time_range':
            time_range_form = WorkSessionTimeRangeForm(request.POST)
            if time_range_form.is_valid():
                work_session = time_range_form.save(commit=False)
                work_session.teacher = teacher
                work_session.entry_type = 'time_range'
                work_session.save()
                from .billing_services import StudentBillingService
                if work_session.student:
                    StudentBillingService.create_bill_item_for_work_session(work_session)
                messages.success(request,
                                 f'Work hours recorded successfully with a time range for {teacher.user.username}!')
                return redirect('record_work_with_teacher', teacher_id=teacher.id)

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
def clock_out(request, session_id):
    """
    Handle clocking out for both teachers and superusers.
    Teachers can only clock out their own sessions,
    while superusers can clock out any teacher's session.
    """
    if request.method == 'POST':
        # Get the session
        session = get_object_or_404(WorkSession, id=session_id, entry_type='clock', clock_out__isnull=True)
        
        # Validate permissions
        if request.user.is_teacher:
            # Teachers can only clock out their own sessions
            if session.teacher.user != request.user:
                raise PermissionDenied("You can only clock out your own sessions.")
        elif not request.user.is_superuser:
            raise PermissionDenied("You don't have permission to clock out sessions.")
        
        # Set clock out time
        session.clock_out = timezone.now()
        session.save()
        
        # Create bill item if there's a student associated
        from .billing_services import StudentBillingService
        if session.student:
            StudentBillingService.create_bill_item_for_work_session(session)
        
        messages.success(request, 'Clocked out successfully!')
        
        # Redirect back to the page we came from
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url:
            return redirect(next_url)
        
        # Default redirect to dashboard
        return redirect('dashboard')


@login_required
def recent_work_sessions(request, teacher_id=None):
    # Superusers and inspectors: must specify a teacher_id
    if request.user.is_superuser or getattr(request.user, 'is_inspector', False):
        if teacher_id is None:
            return HttpResponseForbidden("You must specify a teacher to view sessions for.")
        teacher = get_object_or_404(Teacher, id=teacher_id)
    # Teachers: always see their own sessions
    elif hasattr(request.user, 'teacher'):
        teacher = get_object_or_404(Teacher, user=request.user)
        # Prevent teachers from viewing other teachers' sessions
        if teacher_id is not None and teacher_id != teacher.id:
            return HttpResponseForbidden("You do not have permission to view other teachers' sessions.")
    else:
        return HttpResponseForbidden("You do not have permission to view work sessions.")

    # Fetch all work sessions for the teacher
    work_sessions = WorkSession.objects.filter(teacher=teacher).order_by('-created_at')

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
@user_passes_test(lambda u: u.is_inspector_effective or (hasattr(u, 'teacher') and u.is_authenticated), login_url=None)
def view_salary_report(request, teacher_id, year, month):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    from django.utils import timezone
    from datetime import datetime, timedelta
    # Use timezone-aware datetimes
    start_date = timezone.make_aware(datetime(year, month, 1))
    if month == 12:
        end_date = timezone.make_aware(datetime(year + 1, 1, 1))
    else:
        end_date = timezone.make_aware(datetime(year, month + 1, 1))
    end_date = end_date - timedelta(microseconds=1)

    reports = SalaryReport.objects.filter(
        teacher=teacher,
        start_date__gte=start_date,
        end_date__lte=end_date
    )
    report = reports.first()

    # Calculate the report data - FIXED: Use static method
    report_data = SalaryCalculationService.calculate_salary(teacher, year, month)

    # Permissions: allow inspector, superuser, or the teacher themselves
    if request.user.is_inspector_effective:
        template = 'superuser/view_salary_report.html'
    elif request.user == teacher.user:
        template = 'teachers/view_salary_report.html'
    else:
        raise PermissionDenied("You do not have permission to view this report")

    # Task summary for this report: total hours per task (only for sessions in this report)
    from collections import defaultdict
    task_summary_dict = defaultdict(float)
    if report:
        work_sessions = report.get_work_sessions().order_by('-created_at')
    else:
        work_sessions = WorkSession.objects.filter(teacher=teacher, start_time__gte=start_date, start_time__lte=end_date).order_by('-created_at')
    for ws in work_sessions:
        task_name = ws.task.name
        task_summary_dict[task_name] += float(ws.stored_hours or 0)
    task_summary = [
        {'task_name': name, 'total_hours': hours}
        for name, hours in task_summary_dict.items()
    ]

    return render(request, template, {
        'teacher': teacher,
        'report': report,
        'report_data': report_data,
        'work_sessions': work_sessions,
        'task_summary': task_summary,
    })


@login_required
@user_passes_test(lambda u: u.is_inspector_effective, login_url=None)
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
@user_passes_test(lambda u: u.is_inspector, login_url=None)
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


@login_required
@user_passes_test(lambda u: u.is_superuser)
def view_deactivated_students(request):
    """View all deactivated students"""
    deactivated_students = Student.objects.filter(user__is_active=False)
    context = {
        'deactivated_students': deactivated_students
    }
    return render(request, 'superuser/view_deactivated_students.html', context)


@login_required
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def manage_inspectors(request):
    from .models import Inspector, CustomUser
    from .forms import InspectorCreationForm
    inspectors = Inspector.objects.select_related('user').all()
    can_edit = request.user.is_superuser
    form = InspectorCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid() and can_edit:
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        # Create user
        user = CustomUser.objects.create_user(username=username, email=email, password=password, is_inspector=True)
        Inspector.objects.create(user=user)
        messages.success(request, f'Inspector {username} created successfully.')
        return redirect('manage_inspectors')
    return render(request, 'superuser/manage_inspectors.html', {'form': form, 'inspectors': inspectors, 'can_edit': can_edit})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_inspector(request, inspector_id):
    from .models import Inspector
    inspector = get_object_or_404(Inspector, id=inspector_id)
    if request.method == 'POST':
        username = inspector.user.username
        inspector.user.delete()
        messages.success(request, f'Inspector {username} deleted successfully.')
        return redirect('manage_inspectors')
    return render(request, 'superuser/confirm_delete.html', {'object': inspector, 'object_name': 'inspector'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def change_inspector_password(request, inspector_id):
    from .models import Inspector
    from django.contrib.auth.forms import SetPasswordForm
    inspector = get_object_or_404(Inspector, id=inspector_id)
    if request.method == 'POST':
        form = SetPasswordForm(inspector.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Password for inspector {inspector.user.username} updated successfully.")
            return redirect('manage_inspectors')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SetPasswordForm(inspector.user)
    return render(request, 'superuser/change_password.html', {'form': form, 'inspector': inspector})

# Removed create_salary_report from this file because it belongs in salary_views.py

@login_required
@user_passes_test(lambda u: u.is_inspector_effective, login_url=None)
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
