from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from ..models import CustomUser, Teacher, Task, WorkSession, SalaryReport

class WorkSessionTestCase(TestCase):
    def setUp(self):
        # Create a user with unique username
        username = f"testuser_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        self.user = CustomUser.objects.create_user(
            username=username,
            password='testpass'
        )
        
        # Create a teacher
        self.teacher = Teacher.objects.create(user=self.user)
        
        # Create a task with initial rate
        self.task = Task.objects.create(
            name="Test Task",
            hourly_rate=Decimal('15.00'),
            description="Test task description"
        )

    def test_work_session_stores_initial_rate(self):
        """Test that work session stores the hourly rate at creation time"""
        # Create sessions with different entry types
        sessions = []
        
        # Manual entry session
        session1 = WorkSession.objects.create(
            teacher=self.teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('2.00')
        )
        sessions.append(session1)
        
        # Clock entry session
        clock_in_time = timezone.now()
        clock_out_time = clock_in_time + timezone.timedelta(hours=1.5)
        session2 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='clock',
            clock_in=clock_in_time,
            clock_out=clock_out_time
        )
        session2.save()
        sessions.append(session2)
        
        # Time range entry session
        start_time = clock_out_time + timezone.timedelta(minutes=1)
        end_time = start_time + timezone.timedelta(hours=1.0)
        session3 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='time_range',
            start_time=start_time,
            end_time=end_time
        )
        session3.save()
        sessions.append(session3)
        
        # Verify all sessions stored their hourly rates
        for session in sessions:
            self.assertEqual(session.hourly_rate, Decimal('15.00'))
        
        # Update the task's hourly rate
        self.task.hourly_rate = Decimal('20.00')
        self.task.save()
        
        # Verify all sessions' rates remain unchanged
        for session in sessions:
            session.refresh_from_db()
            self.assertEqual(session.hourly_rate, Decimal('15.00'))

    def test_salary_report_uses_stored_rates(self):
        """Test that salary report uses stored rates from work sessions"""
        # Create sessions with different entry types and rates
        sessions = []
        
        # First set of sessions at rate 15
        session1 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('2.00')
        )
        session1.save()
        sessions.append(session1)
        
        # Clock entry session
        clock_in_time = timezone.now()
        clock_out_time = clock_in_time + timezone.timedelta(hours=1.5)
        session2 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='clock',
            clock_in=clock_in_time,
            clock_out=clock_out_time
        )
        session2.save()
        sessions.append(session2)
        
        # Time range entry session
        start_time = clock_out_time + timezone.timedelta(minutes=1)
        end_time = start_time + timezone.timedelta(hours=1.0)
        session3 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='time_range',
            start_time=start_time,
            end_time=end_time
        )
        session3.save()
        sessions.append(session3)
        
        # Update rate to 20
        self.task.hourly_rate = Decimal('20.00')
        self.task.save()
        
        # Second set of sessions at rate 20
        session4 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('1.0')
        )
        session4.save()
        sessions.append(session4)
        
        # Clock entry session (second set)
        clock_in_time_2 = end_time + timezone.timedelta(minutes=1)
        clock_out_time_2 = clock_in_time_2 + timezone.timedelta(hours=2.0)
        session5 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='clock',
            clock_in=clock_in_time_2,
            clock_out=clock_out_time_2
        )
        session5.save()
        sessions.append(session5)
        
        # Time range entry session (second set)
        start_time_2 = clock_out_time_2 + timezone.timedelta(minutes=1)
        end_time_2 = start_time_2 + timezone.timedelta(hours=1.5)
        session6 = WorkSession(
            teacher=self.teacher,
            task=self.task,
            entry_type='time_range',
            start_time=start_time_2,
            end_time=end_time_2
        )
        session6.save()
        sessions.append(session6)
        
        # Create a salary report
        report = SalaryReport.create_for_month(
            teacher=self.teacher,
            year=timezone.now().year,
            month=timezone.now().month,
            created_by=self.user
        )
        
        # Verify total hours
        total_hours = sum(session.stored_hours for session in sessions)
        self.assertEqual(report.total_hours, total_hours)
        
        # Verify total amount uses stored rates
        total_amount = sum(session.total_amount for session in sessions)
        self.assertEqual(report.total_amount, total_amount)
        
        # Verify individual session calculations
        self.assertEqual(session1.calculated_amount, Decimal('30.00'))  # 2 hours * $15
        self.assertEqual(session2.calculated_amount, Decimal('30.00'))  # 2 hours * $15 (rounded)
        self.assertEqual(session3.calculated_amount, Decimal('15.00'))  # 1 hour * $15
        self.assertEqual(session4.calculated_amount, Decimal('20.00'))  # 1 hour * $20
        self.assertEqual(session5.calculated_amount, Decimal('40.00'))  # 2 hours * $20
        self.assertEqual(session6.calculated_amount, Decimal('40.00'))  # 2 hours * $20 (rounded)
