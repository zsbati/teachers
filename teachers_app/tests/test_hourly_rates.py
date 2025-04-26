import os
import django
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from teachers_app.models import CustomUser, Teacher, Task, WorkSession, SalaryReport

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teachers.settings')
django.setup()

def test_hourly_rates():
    print("Starting hourly rate tests...")
    
    # Create a unique username
    username = f"testuser_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create a user
    user = CustomUser.objects.create_user(
        username=username,
        password='testpass'
    )
    
    # Create a teacher
    teacher = Teacher.objects.create(user=user)
    
    # Create a task with initial rate
    task = Task.objects.create(
        name="Test Task",
        hourly_rate=Decimal('15.00'),
        description="Test task description"
    )
    
    print("\nTest 1: Creating work sessions with different entry types")
    
    # Manual entry
    session1 = WorkSession.objects.create(
        teacher=teacher,
        task=task,
        entry_type='manual',
        manual_hours=Decimal('2.00')
    )
    print(f"Session 1 (manual) hourly rate: ${session1.hourly_rate}")
    
    # Clock entry
    now = timezone.now()
    session2 = WorkSession.objects.create(
        teacher=teacher,
        task=task,
        entry_type='clock',
        clock_in=now,
        clock_out=now + timezone.timedelta(hours=1.5)
    )
    print(f"Session 2 (clock) hourly rate: ${session2.hourly_rate}")
    
    # Time range entry
    session3 = WorkSession.objects.create(
        teacher=teacher,
        task=task,
        entry_type='time_range',
        start_time=now,
        end_time=now + timezone.timedelta(hours=1.0)
    )
    print(f"Session 3 (time_range) hourly rate: ${session3.hourly_rate}")
    
    print("\nTest 2: Updating task rate")
    # Update the task's hourly rate
    task.hourly_rate = Decimal('20.00')
    task.save()
    
    print("\nTest 3: Creating new sessions with updated rate")
    # Create new sessions with updated rate
    session4 = WorkSession.objects.create(
        teacher=teacher,
        task=task,
        entry_type='manual',
        manual_hours=Decimal('1.0')
    )
    print(f"Session 4 (manual) hourly rate: ${session4.hourly_rate}")
    
    session5 = WorkSession.objects.create(
        teacher=teacher,
        task=task,
        entry_type='clock',
        clock_in=now,
        clock_out=now + timezone.timedelta(hours=2.0)
    )
    print(f"Session 5 (clock) hourly rate: ${session5.hourly_rate}")
    
    session6 = WorkSession.objects.create(
        teacher=teacher,
        task=task,
        entry_type='time_range',
        start_time=now,
        end_time=now + timezone.timedelta(hours=1.5)
    )
    print(f"Session 6 (time_range) hourly rate: ${session6.hourly_rate}")
    
    print("\nTest 4: Creating salary report")
    report = SalaryReport.create_for_month(
        teacher=teacher,
        year=timezone.now().year,
        month=timezone.now().month,
        created_by=user
    )
    
    print("\nResults:")
    print(f"Total hours: {report.total_hours}")
    print(f"Total amount: ${report.total_amount}")
    
    print("\nIndividual session amounts:")
    print(f"Session 1 (manual): ${session1.calculated_amount}")
    print(f"Session 2 (clock): ${session2.calculated_amount}")
    print(f"Session 3 (time_range): ${session3.calculated_amount}")
    print(f"Session 4 (manual): ${session4.calculated_amount}")
    print(f"Session 5 (clock): ${session5.calculated_amount}")
    print(f"Session 6 (time_range): ${session6.calculated_amount}")
    
    print("\nTest 5: Deleting the task and verifying report")
    # Delete the task
    task.delete()
    
    # Create another salary report
    report2 = SalaryReport.create_for_month(
        teacher=teacher,
        year=timezone.now().year,
        month=timezone.now().month,
        created_by=user
    )
    
    print("\nResults after task deletion:")
    print(f"Total hours: {report2.total_hours}")
    print(f"Total amount: ${report2.total_amount}")
    
    # Clean up
    session1.delete()
    session2.delete()
    session3.delete()
    session4.delete()
    session5.delete()
    session6.delete()
    teacher.delete()
    user.delete()

if __name__ == '__main__':
    test_hourly_rates()
