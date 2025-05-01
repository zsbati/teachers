from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from teachers_app.models import Task, WorkSession, Teacher, Student, CustomUser
from teachers_app.billing_models import Bill, BillItem
from teachers_app.billing_services import StudentBillingService
from django.db.models import Sum
from datetime import datetime, timedelta
from django.apps import apps
from teachers_app.apps import TeachersAppConfig

class BillingTests(TestCase):
    def setUp(self):
        # Create a test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a teacher and student
        self.teacher = Teacher.objects.create(user=user)
        self.student = Student.objects.create(user=user)
        
        # Create tasks with different prices
        self.free_task = Task.objects.create(
            name='Free Task',
            description='Free service',
            price=Decimal('0.00'),
            hourly_rate=Decimal('7.50')
        )
        
        self.paid_task = Task.objects.create(
            name='Paid Task',
            description='Paid service',
            price=Decimal('20.00'),
            hourly_rate=Decimal('7.50')
        )

    def test_free_task_billing(self):
        """Test that free tasks don't appear in bill items"""
        # Create a work session with free task
        work_session = WorkSession.objects.create(
            task=self.free_task,
            teacher=self.teacher,
            student=self.student,
            entry_type='manual',
            manual_hours=1.0,
            stored_hours=1.0
        )
        
        # Create bill item
        bill_item = StudentBillingService.create_bill_item_for_work_session(work_session)
        self.assertIsNotNone(bill_item)
        
        # Check that bill item has zero price and amount
        self.assertEqual(bill_item.service_price_at_billing, Decimal('0.00'))
        self.assertEqual(bill_item.amount, Decimal('0.00'))
        
        # Get bill items for student
        bill_items = BillItem.objects.filter(
            bill__student=self.student,
            service_price_at_billing__gt=0,
            amount__gt=0
        )
        
        # Should be empty since we filtered out zero prices
        self.assertEqual(bill_items.count(), 0)

    def test_paid_task_billing(self):
        """Test that paid tasks appear in bill items"""
        # Create a work session with paid task
        work_session = WorkSession.objects.create(
            task=self.paid_task,
            teacher=self.teacher,
            student=self.student,
            entry_type='manual',
            manual_hours=1.0,
            stored_hours=1.0
        )
        
        # Create bill item
        bill_item = StudentBillingService.create_bill_item_for_work_session(work_session)
        self.assertIsNotNone(bill_item)
        
        # Check that bill item has correct price and amount
        self.assertEqual(bill_item.service_price_at_billing, Decimal('20.00'))
        self.assertEqual(bill_item.amount, Decimal('20.00'))
        
        # Get bill items for student
        bill_items = BillItem.objects.filter(
            bill__student=self.student,
            service_price_at_billing__gt=0,
            amount__gt=0
        )
        
        # Should have one item since it's a paid service
        self.assertEqual(bill_items.count(), 1)
        self.assertEqual(bill_items[0].service_price_at_billing, Decimal('20.00'))
        self.assertEqual(bill_items[0].amount, Decimal('20.00'))

    def test_total_amount_calculation(self):
        """Test that total amount only includes non-zero items"""
        # Create work sessions for both tasks
        free_session = WorkSession.objects.create(
            task=self.free_task,
            teacher=self.teacher,
            student=self.student,
            entry_type='manual',
            manual_hours=1.0,
            stored_hours=1.0
        )
        
        paid_session = WorkSession.objects.create(
            task=self.paid_task,
            teacher=self.teacher,
            student=self.student,
            entry_type='manual',
            manual_hours=1.0,
            stored_hours=1.0
        )
        
        # Create bill items
        StudentBillingService.create_bill_item_for_work_session(free_session)
        paid_bill_item = StudentBillingService.create_bill_item_for_work_session(paid_session)
        
        # Get the bill
        bill = paid_bill_item.bill
        
        # Check total amount calculation
        bill.refresh_from_db()
        self.assertEqual(bill.total_amount, Decimal('20.00'))  # Only paid task should count

if __name__ == '__main__':
    import unittest
    unittest.main()
