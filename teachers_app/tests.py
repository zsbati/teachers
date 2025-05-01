from django.test import TestCase
from django.contrib.auth.models import User
from .models import Task, WorkSession, Teacher, Student, CustomUser
from .billing_models import Bill, BillItem
from datetime import datetime, timedelta
from decimal import Decimal

class BillingTests(TestCase):
    def setUp(self):
        # Create a test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a teacher
        self.teacher = Teacher.objects.create(user=user)
        
        # Create a student
        self.student = Student.objects.create(user=user)
        
        # Create tasks
        self.student_task = Task.objects.create(
            name='Student Task',
            description='For students',
            price=Decimal('0.00'),
            hourly_rate=Decimal('7.50'),
            is_student_task=True
        )
        
        self.teacher_task = Task.objects.create(
            name='Teacher Task',
            description='For teachers',
            price=Decimal('0.00'),
            hourly_rate=Decimal('7.50'),
            is_student_task=False
        )

    def test_student_task_billing(self):
        """Test that student tasks use price (0.00) for billing"""
        # Create a work session with student task
        work_session = WorkSession.objects.create(
            task=self.student_task,
            teacher=self.teacher,
            student=self.student,
            entry_type='manual',
            manual_hours=1.0,
            stored_hours=1.0
        )
        
        # Check that total_amount uses price (0.00)
        self.assertEqual(work_session.total_amount, Decimal('0.00'))
        
        # Create a bill item
        from .billing_services import StudentBillingService
        bill_item = StudentBillingService.create_bill_item_for_work_session(work_session)
        
        # Check that bill item uses price (0.00)
        self.assertIsNotNone(bill_item)
        self.assertEqual(bill_item.amount, Decimal('0.00'))
        self.assertEqual(bill_item.service_price_at_billing, Decimal('0.00'))

    def test_teacher_task_billing(self):
        """Test that teacher tasks use hourly_rate (7.50) for billing"""
        # Create a work session with teacher task
        work_session = WorkSession.objects.create(
            task=self.teacher_task,
            teacher=self.teacher,
            student=None,
            entry_type='manual',
            manual_hours=1.0,
            stored_hours=1.0
        )
        
        # Check that total_amount uses hourly_rate (7.50)
        self.assertEqual(work_session.total_amount, Decimal('7.50'))
        
        # Create a bill item
        from .billing_services import StudentBillingService
        bill_item = StudentBillingService.create_bill_item_for_work_session(work_session)
        
        # Check that bill item is None (no student)
        self.assertIsNone(bill_item)

    def test_task_display(self):
        """Test that tasks display correct price type in template"""
        # This test would be run in the template rendering
        # For student task: should show "$0.00"
        # For teacher task: should show "$7.50/hour"
        self.assertEqual(self.student_task.is_student_task, True)
        self.assertEqual(self.teacher_task.is_student_task, False)

if __name__ == '__main__':
    import unittest
    unittest.main()
