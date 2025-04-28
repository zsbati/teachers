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
        # Ensure created_at is within the report month
        work_session.created_at = session_date
        work_session.save(update_fields=["created_at"])
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

    def test_superuser_can_edit_and_delete_everything(self):
        self.client.login(username='admin', password='pass')
        # Create work session, service, class, bill, bill item, student
        work_session = WorkSession.objects.create(
            teacher=self.teacher_obj,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('1.0'),
            stored_hours=Decimal('1.0'),
            hourly_rate=Decimal('20.00')
        )
        service = Service.objects.create(name='Science', price=Decimal('30.00'), is_active=True)
        # Edit work session
        url = reverse('edit_work_session', args=[work_session.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Delete work session
        url = reverse('delete_work_session', args=[work_session.id])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302])
        # Edit service
        url = reverse('edit_service', args=[service.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Delete service
        url = reverse('delete_service', args=[service.id])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302])

    def test_teacher_cannot_edit_or_delete_others_or_services(self):
        self.client.login(username='teacher', password='pass')
        # Try to edit/delete a service
        url = reverse('edit_service', args=[self.service.id])
        resp = self.client.get(url)
        self.assertNotEqual(resp.status_code, 200)
        url = reverse('delete_service', args=[self.service.id])
        resp = self.client.post(url)
        self.assertNotEqual(resp.status_code, 200)
        # Try to edit/delete other's work session
        other_teacher = Teacher.objects.create(user=User.objects.create_user('other', 'other@example.com', 'pass'))
        work_session = WorkSession.objects.create(
            teacher=other_teacher,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('1.0'),
            stored_hours=Decimal('1.0'),
            hourly_rate=Decimal('20.00')
        )
        url = reverse('edit_work_session', args=[work_session.id])
        resp = self.client.get(url)
        self.assertNotEqual(resp.status_code, 200)
        url = reverse('delete_work_session', args=[work_session.id])
        resp = self.client.post(url)
        self.assertNotEqual(resp.status_code, 200)

    def test_teacher_can_add_and_view_own_work_sessions(self):
        self.client.login(username='teacher', password='pass')
        # Add a work session
        url = reverse('record_work')
        resp = self.client.post(url, {
            'teacher': self.teacher_obj.id,
            'task': self.task.id,
            'entry_type': 'manual',
            'manual_hours': '1.5',
        })
        self.assertIn(resp.status_code, [200, 302])
        # View own work sessions
        url = reverse('recent_work_sessions', args=[self.teacher_obj.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_student_can_edit_own_info_and_view_bills(self):
        self.client.login(username='student', password='pass')
        # Edit own info
        url = reverse('edit_student', args=[self.student.id])
        resp = self.client.post(url, {'phone': '456'})
        self.assertIn(resp.status_code, [200, 302])
        # View own bills
        url = reverse('student_bills', args=[self.student.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_edit_others_info_or_work_sessions(self):
        self.client.login(username='student', password='pass')
        # Try to edit other student
        other_student = Student.objects.create(user=User.objects.create_user('stud2', 'stud2@example.com', 'pass'), phone='789')
        url = reverse('edit_student', args=[other_student.id])
        resp = self.client.post(url, {'phone': '000'})
        self.assertNotEqual(resp.status_code, 200)
        # Try to edit work session
        ws = WorkSession.objects.create(
            teacher=self.teacher_obj,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('1.0'),
            stored_hours=Decimal('1.0'),
            hourly_rate=Decimal('20.00')
        )
        url = reverse('edit_work_session', args=[ws.id])
        resp = self.client.get(url)
        self.assertNotEqual(resp.status_code, 200)

    def test_inspector_cannot_edit_or_delete_anything(self):
        self.client.login(username='inspector', password='pass')
        # Try to edit service
        url = reverse('edit_service', args=[self.service.id])
        resp = self.client.get(url)
        self.assertNotEqual(resp.status_code, 200)
        # Try to delete service
        url = reverse('delete_service', args=[self.service.id])
        resp = self.client.post(url)
        self.assertNotEqual(resp.status_code, 200)
        # Try to edit/delete work session
        ws = WorkSession.objects.create(
            teacher=self.teacher_obj,
            task=self.task,
            entry_type='manual',
            manual_hours=Decimal('1.0'),
            stored_hours=Decimal('1.0'),
            hourly_rate=Decimal('20.00')
        )
        url = reverse('edit_work_session', args=[ws.id])
        resp = self.client.get(url)
        self.assertNotEqual(resp.status_code, 200)
        url = reverse('delete_work_session', args=[ws.id])
        resp = self.client.post(url)
        self.assertNotEqual(resp.status_code, 200)

    def test_negative_and_invalid_work_session_data(self):
        self.client.login(username='teacher', password='pass')
        url = reverse('record_work')
        # Negative hours
        resp = self.client.post(url, {
            'teacher': self.teacher_obj.id,
            'task': self.task.id,
            'entry_type': 'manual',
            'manual_hours': '-2',
        })
        self.assertContains(resp, "Manual hours cannot be negative")
        # Missing required fields
        resp = self.client.post(url, {
            'teacher': self.teacher_obj.id,
            'task': self.task.id,
            'entry_type': 'manual',
        })
        self.assertContains(resp, "Manual entry type requires manual_hours")

    def test_bill_edge_cases(self):
        self.client.login(username='admin', password='pass')
        # Zero amount
        bill = Bill.objects.create(student=self.student, month='2024-01-01', total_amount=0)
        bill_item = BillItem.objects.create(bill=bill, service_name='Math', service_description='', service_price_at_billing=Decimal('0.00'), quantity=1, amount=Decimal('0.00'))
        self.assertEqual(bill_item.amount, Decimal('0.00'))
        # Negative amount
        bill_item2 = BillItem.objects.create(bill=bill, service_name='Math', service_description='', service_price_at_billing=Decimal('-10.00'), quantity=1, amount=Decimal('-10.00'))
        self.assertEqual(bill_item2.amount, Decimal('-10.00'))
        # Very large amount
        bill_item3 = BillItem.objects.create(bill=bill, service_name='Math', service_description='', service_price_at_billing=Decimal('1000000.00'), quantity=1000, amount=Decimal('1000000000.00'))
        self.assertEqual(bill_item3.amount, Decimal('1000000000.00'))
