from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
from teachers_app.models import CustomUser, Teacher, Task, WorkSession, SalaryReport

class RateChangeTestCase(TestCase):
    def setUp(self):
        # Create a user with unique username
        username = f"testuser_{timezone.now().strftime('%Y%m%d_%H%M%S')}_rates"
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
            price=Decimal('15.00')
        )

    def test_rate_changes_across_months(self):
        """Test rate changes across different months"""
        # Create sessions in January with rate 15
        january = timezone.make_aware(datetime(timezone.now().year, 1, 15))
        
        # January sessions
        jan_session1 = WorkSession.objects.create(
            teacher=self.teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('2.00'),
            created_at=january
        )
        
        # Change rate in February
        february = timezone.make_aware(datetime(timezone.now().year, 2, 15))
        self.task.hourly_rate = Decimal('20.00')
        self.task.price = Decimal('20.00')
        self.task.save()
        
        # February sessions
        feb_session1 = WorkSession.objects.create(
            teacher=self.teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('1.00'),
            created_at=february
        )
        
        # Create salary reports for both months
        jan_report = SalaryReport.create_for_month(
            teacher=self.teacher,
            year=timezone.now().year,
            month=1,
            created_by=self.user
        )
        
        feb_report = SalaryReport.create_for_month(
            teacher=self.teacher,
            year=timezone.now().year,
            month=2,
            created_by=self.user
        )
        
        # Verify January report (should use rate 15)
        self.assertEqual(jan_report.total_hours, Decimal('2.00'))
        self.assertEqual(jan_report.total_amount, Decimal('30.00'))
        self.assertEqual(jan_session1.teacher_payment_amount, Decimal('30.00'))
        self.assertEqual(jan_session1.total_amount, Decimal('30.00'))  # Student billing
        
        # Verify February report (should use rate 20)
        self.assertEqual(feb_report.total_hours, Decimal('1.00'))
        self.assertEqual(feb_report.total_amount, Decimal('20.00'))
        self.assertEqual(feb_session1.teacher_payment_amount, Decimal('20.00'))
        self.assertEqual(feb_session1.total_amount, Decimal('20.00'))  # Student billing

    def test_rate_changes_within_month(self):
        """Test rate changes within the same month"""
        # Create sessions in January with rate 15
        january = timezone.make_aware(datetime(timezone.now().year, 1, 15))
        jan_session1 = WorkSession.objects.create(
            teacher=self.teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('2.00'),
            created_at=january
        )
        
        # Change rate in January (but later date)
        january_later = timezone.make_aware(datetime(timezone.now().year, 1, 20))
        self.task.hourly_rate = Decimal('20.00')
        self.task.price = Decimal('20.00')
        self.task.save()
        
        # Create another session with new rate
        jan_session2 = WorkSession.objects.create(
            teacher=self.teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('1.00'),
            created_at=january_later
        )
        
        # Create salary report for January
        report = SalaryReport.create_for_month(
            teacher=self.teacher,
            year=timezone.now().year,
            month=1,
            created_by=self.user
        )
        
        # Verify report totals (should include both rates)
        self.assertEqual(report.total_hours, Decimal('3.00'))
        self.assertEqual(report.total_amount, Decimal('50.00'))  # 2*15 + 1*20
        self.assertEqual(jan_session1.teacher_payment_amount, Decimal('30.00'))
        self.assertEqual(jan_session1.total_amount, Decimal('30.00'))  # Student billing
        self.assertEqual(jan_session2.teacher_payment_amount, Decimal('20.00'))
        self.assertEqual(jan_session2.total_amount, Decimal('20.00'))  # Student billing

    def test_partial_month_sessions(self):
        """Test sessions that span across month boundaries"""
        # Create session that starts in January and ends in February
        january_end = timezone.make_aware(datetime(timezone.now().year, 1, 31, 23, 59))
        february_start = timezone.make_aware(datetime(timezone.now().year, 2, 1, 0, 1))
        
        # Create a time range session that spans months
        session = WorkSession.objects.create(
            teacher=self.teacher,
            task=self.task,
            entry_type='time_range',
            start_time=january_end,
            end_time=february_start,
            stored_hours=Decimal('1.00')  # Manually set stored_hours for testing
        )
        
        # Create salary reports for both months
        jan_report = SalaryReport.create_for_month(
            teacher=self.teacher,
            year=timezone.now().year,
            month=1,
            created_by=self.user
        )
        
        feb_report = SalaryReport.create_for_month(
            teacher=self.teacher,
            year=timezone.now().year,
            month=2,
            created_by=self.user
        )
        
        # Verify both reports include the session
        self.assertEqual(jan_report.total_hours, Decimal('1.00'))
        self.assertEqual(feb_report.total_hours, Decimal('1.00'))
        self.assertEqual(jan_report.total_amount, Decimal('15.00'))
        self.assertEqual(feb_report.total_amount, Decimal('15.00'))

    def test_rate_changes_with_free_tasks(self):
        """Test rate changes with free tasks (price=0)"""
        # Create a free task
        free_task = Task.objects.create(
            name="Free Task",
            hourly_rate=Decimal('15.00'),
            price=Decimal('0.00')
        )
        
        # Create a session with free task
        session = WorkSession.objects.create(
            teacher=self.teacher,
            task=free_task,
            entry_type='manual',
            manual_hours=Decimal('2.00')
        )
        
        # Change task rate (shouldn't affect free task)
        free_task.hourly_rate = Decimal('20.00')
        free_task.save()
        
        # Create salary report
        report = SalaryReport.create_for_month(
            teacher=self.teacher,
            year=timezone.now().year,
            month=1,
            created_by=self.user
        )
        
        # Verify payment amount (should use original rate)
        self.assertEqual(session.teacher_payment_amount, Decimal('30.00'))
        self.assertEqual(session.total_amount, Decimal('0.00'))  # Free task for student
        self.assertEqual(report.total_amount, Decimal('30.00'))
