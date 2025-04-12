from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import (
    CustomPasswordChangeForm, TeacherCreationForm, TaskForm,
    WorkSessionManualForm, WorkSessionClockForm
)
from .models import Teacher, CustomUser, Task, WorkSession

def is_superuser(user):
    return user.is_superuser

def is_teacher(user):
    return user.is_teacher

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

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
@user_passes_test(is_superuser)
def manage_teachers(request):
    teachers = Teacher.objects.all()
    form = TeacherCreationForm()
    return render(request, 'manage_teachers.html', {
        'teachers': teachers,
        'form': form
    })

@login_required
@user_passes_test(is_superuser)
def add_teacher(request):
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            # Create user
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
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
    return redirect('manage_teachers')

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
def manage_tasks(request):
    tasks = Task.objects.all()
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task was successfully added!')
            return redirect('manage_tasks')
    else:
        form = TaskForm()
    
    return render(request, 'manage_tasks.html', {
        'tasks': tasks,
        'form': form
    })

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
@user_passes_test(is_teacher)
def record_work(request):
    if request.method == 'POST':
        entry_type = request.POST.get('entry_type')
        if entry_type == 'manual':
            form = WorkSessionManualForm(request.POST)
            if form.is_valid():
                work_session = form.save(commit=False)
                work_session.teacher = request.user.teacher
                work_session.entry_type = 'manual'
                work_session.save()
                messages.success(request, 'Work hours recorded successfully!')
                return redirect('record_work')
        elif entry_type == 'clock':
            form = WorkSessionClockForm(request.POST)
            if form.is_valid():
                work_session = form.save(commit=False)
                work_session.teacher = request.user.teacher
                work_session.entry_type = 'clock'
                work_session.clock_in = timezone.now()
                work_session.save()
                messages.success(request, 'Clock-in recorded successfully!')
                return redirect('record_work')
    else:
        manual_form = WorkSessionManualForm()
        clock_form = WorkSessionClockForm()
    
    active_session = WorkSession.objects.filter(
        teacher=request.user.teacher,
        entry_type='clock',
        clock_out__isnull=True
    ).first()
    
    completed_sessions = WorkSession.objects.filter(
        teacher=request.user.teacher
    ).exclude(
        id=active_session.id if active_session else None
    ).order_by('-created_at')[:10]
    
    return render(request, 'record_work.html', {
        'manual_form': manual_form,
        'clock_form': clock_form,
        'active_session': active_session,
        'completed_sessions': completed_sessions
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