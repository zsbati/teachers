from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from teachers_app.models import CustomUser, Teacher, Task, WorkSession, SalaryReport

class Command(BaseCommand):
    help = 'Test the hourly rate functionality of work sessions'

    def handle(self, *args, **options):
        print("Starting hourly rate tests...")
        
        # Create a user
        user = CustomUser.objects.create_user(
            username='testuser',
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
        
        print("\nTest 1: Creating work session with initial rate")
        # Create a work session
        session1 = WorkSession.objects.create(
            teacher=teacher,
            task=task,
            entry_type='manual',
            manual_hours=Decimal('2.00')
        )
        print(f"Session 1 hourly rate: ${session1.hourly_rate}")
        
        print("\nTest 2: Updating task rate and creating new session")
        # Update the task's hourly rate
        task.hourly_rate = Decimal('20.00')
        task.save()
        
        # Create a new session
        session2 = WorkSession.objects.create(
            teacher=teacher,
            task=task,
            entry_type='manual',
            manual_hours=Decimal('1.50')
        )
        print(f"Session 1 hourly rate (after update): ${session1.hourly_rate}")
        print(f"Session 2 hourly rate: ${session2.hourly_rate}")
        
        print("\nTest 3: Creating salary report")
        # Create a salary report
        report = SalaryReport.create_for_month(
            teacher=teacher,
            year=timezone.now().year,
            month=timezone.now().month,
            created_by=user
        )
        
        print("\nResults:")
        print(f"Total hours: {report.total_hours}")
        print(f"Total amount: ${report.total_amount}")
        print(f"Session 1 amount: ${session1.calculated_amount}")
        print(f"Session 2 amount: ${session2.calculated_amount}")
        
        # Clean up
        session1.delete()
        session2.delete()
        task.delete()
        teacher.delete()
        user.delete()
