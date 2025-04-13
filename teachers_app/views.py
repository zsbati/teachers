from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseForbidden
from .forms import (
    CustomPasswordChangeForm, TeacherCreationForm, TaskForm,
    WorkSessionManualForm, WorkSessionClockForm, WorkSessionTimeRangeForm, WorkSessionFilterForm, AddTeacherForm
)
from .models import Teacher, CustomUser, Task, WorkSession


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
@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_teachers(request):
    if request.method == "POST":
        form = AddTeacherForm(request.POST)
        if form.is_valid():
            form.save()
            print("Teacher added successfully!")
        else:
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
            form.save()
            print("Task added successfully!")  # Debugging
        else:
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
@user_passes_test(is_superuser)
def remove_teacher(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, id=teacher_id)
        user = teacher.user
        teacher.delete()
        user.delete()
        messages.success(request, 'Teacher was successfully removed!')
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
