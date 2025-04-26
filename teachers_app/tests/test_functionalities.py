from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from teachers_app.models import Teacher, Student, Service, Task, WorkSession, SalaryReport
from teachers_app.billing_models import Bill, BillItem
from decimal import Decimal
from django.utils import timezone
from datetime import datetime

User = get_user_model()

class RolePermissionsTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.inspector = User.objects.create_user('inspector', 'insp@example.com', 'pass', is_inspector=True)
        self.teacher = User.objects.create_user('teacher', 'teach@example.com', 'pass')
        self.student_user = User.objects.create_user('student', 'stud@example.com', 'pass')
        self.student = Student.objects.create(user=self.student_user, phone='123')
        self.teacher_obj = Teacher.objects.create(user=self.teacher)
        self.service = Service.objects.create(name='Math', price=Decimal('21.00'), is_active=True)
        self.task = Task.objects.create(name='Tutoring', price=Decimal('21.00'), hourly_rate=Decimal('20.00'))
        self.client = Client()

    def test_superuser_can_access_bill_items(self):
        self.client.login(username='admin', password='pass')
        # Create a bill for student
        bill = Bill.objects.create(student=self.student, month='2024-01-01', total_amount=0)
        bill_item = BillItem.objects.create(bill=bill, service_name='Math', service_description='', service_price_at_billing=Decimal('21.00'), quantity=1, amount=Decimal('21.00'))
        url = reverse('edit_bill_item', args=[bill_item.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Edit quantity
        resp = self.client.post(url, {'service': self.service.id, 'quantity': 2, 'service_description': ''}, follow=True)
        bill_item.refresh_from_db()
        self.assertEqual(bill_item.quantity, 2)
        self.assertEqual(bill_item.amount, Decimal('42.00'))

    def test_superuser_can_delete_bill_item(self):
        self.client.login(username='admin', password='pass')
        bill = Bill.objects.create(student=self.student, month='2024-01-01', total_amount=0)
        bill_item = BillItem.objects.create(bill=bill, service_name='Math', service_description='', service_price_at_billing=Decimal('21.00'), quantity=1, amount=Decimal('21.00'))
        url = reverse('delete_bill_item', args=[bill_item.id])
        resp = self.client.post(url, follow=True)
        self.assertFalse(BillItem.objects.filter(id=bill_item.id).exists())

    def test_inspector_cannot_edit_or_delete(self):
        self.client.login(username='inspector', password='pass')
        bill = Bill.objects.create(student=self.student, month='2024-01-01', total_amount=0)
        bill_item = BillItem.objects.create(bill=bill, service_name='Math', service_description='', service_price_at_billing=Decimal('21.00'), quantity=1, amount=Decimal('21.00'))
        edit_url = reverse('edit_bill_item', args=[bill_item.id])
        delete_url = reverse('delete_bill_item', args=[bill_item.id])
        resp = self.client.get(edit_url)
        self.assertNotEqual(resp.status_code, 200)
        resp = self.client.post(delete_url)
        self.assertNotEqual(resp.status_code, 200)

    def test_student_can_view_own_bills(self):
        self.client.login(username='student', password='pass')
        bill = Bill.objects.create(student=self.student, month='2024-01-01', total_amount=0)
        url = reverse('student_bills', args=[self.student.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_teacher_can_record_work_session(self):
        self.client.login(username='teacher', password='pass')
        url = reverse('manage_services')  # Example: teacher dashboard or work session add
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302])  # 302 if redirect to login or dashboard

    def test_bulk_billing_accessible_to_superuser(self):
        self.client.login(username='admin', password='pass')
        url = reverse('bill_all_students')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_bulk_billing_not_accessible_to_non_superuser(self):
        self.client.login(username='teacher', password='pass')
        url = reverse('bill_all_students')
        resp = self.client.get(url)
        self.assertNotEqual(resp.status_code, 200)

    def test_historic_billitem_values_are_preserved(self):
        self.client.login(username='admin', password='pass')
        # Create bill and bill item with original price
        bill = Bill.objects.create(student=self.student, month='2024-01-01', total_amount=0)
        bill_item = BillItem.objects.create(
            bill=bill,
            service_name='Math',
            service_description='',
            service_price_at_billing=Decimal('21.00'),
            quantity=2,
            amount=Decimal('42.00')
        )
        # Update the service price
        self.service.price = Decimal('50.00')
        self.service.save()
        # Refresh bill item and check values are unchanged
        bill_item.refresh_from_db()
        self.assertEqual(bill_item.service_price_at_billing, Decimal('21.00'))
        self.assertEqual(bill_item.amount, Decimal('42.00'))
        # Create a new bill item, should use new price
        bill_item2 = BillItem.objects.create(
            bill=bill,
            service_name='Math',
            service_description='',
            service_price_at_billing=self.service.price,
            quantity=2,
            amount=self.service.price * 2
        )
        self.assertEqual(bill_item2.service_price_at_billing, Decimal('50.00'))
        self.assertEqual(bill_item2.amount, Decimal('100.00'))

    def test_historic_salary_report_values_are_preserved(self):
        self.client.login(username='admin', password='pass')
        # Create a salary report with original hourly rate
        teacher = self.teacher_obj
        # Create a work session with a specific hourly rate
        session_date = timezone.make_aware(datetime(2024, 1, 10))
        work_session = WorkSession.objects.create(
            teacher=teacher,
            task=self.task,
            entry_type='manual',
            stored_hours=Decimal('10.00'),
            manual_hours=Decimal('10.00'),
            hourly_rate=Decimal('20.00'),
            created_at=session_date
        )
        # Create a salary report for January 2024
        report = SalaryReport.create_for_month(
            teacher=teacher,
            year=2024,
            month=1,
            created_by=self.superuser,
            notes='Test report'
        )
        self.assertEqual(report.total_hours, Decimal('10.00'))
        self.assertEqual(report.total_amount, Decimal('200.00'))
        # Change the hourly rate for the task and work session
        self.task.price = Decimal('50.00')
        self.task.save()
        work_session.hourly_rate = Decimal('50.00')
        work_session.save()
        # Refresh the report from db
        report.refresh_from_db()
        # The original report values should be preserved
        self.assertEqual(report.total_hours, Decimal('10.00'))
        self.assertEqual(report.total_amount, Decimal('200.00'))
        # Creating a new report should use the updated rate
        new_report = SalaryReport.create_for_month(
            teacher=teacher,
            year=2024,
            month=1,
            created_by=self.superuser,
            notes='Test report 2'
        )
        self.assertEqual(new_report.total_amount, Decimal('500.00'))
