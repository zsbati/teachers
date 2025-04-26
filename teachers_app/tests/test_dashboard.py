from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from teachers_app.models import CustomUser, Teacher, Task, WorkSession, SalaryReport, Inspector

class DashboardTestCase(TestCase):
    def setUp(self):
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        # Create superuser
        self.superuser = CustomUser.objects.create_superuser(
            username=f'superuser_{timestamp}',
            password='testpass',
            email=f'super_{timestamp}@test.com'
        )

        # Create inspector
        self.inspector_user = CustomUser.objects.create_user(
            username=f'inspector_{timestamp}',
            password='testpass',
            email=f'inspector_{timestamp}@test.com'
        )
        self.inspector = Inspector.objects.create(user=self.inspector_user)

        # Create regular user/teacher
        self.regular_user = CustomUser.objects.create_user(
            username=f'regular_{timestamp}',
            password='testpass'
        )
        self.teacher = Teacher.objects.create(user=self.regular_user)

    def test_dashboard_data(self):
        print("\nTest 1: Create test data for dashboard")
        # [Previous task and work session creation code remains the same]

        print("\nTest 2: Create salary report")
        # [Previous salary report creation code remains the same]

        print("\nTest 3: Verify user permissions")
        print(f"Superuser has staff status: {self.superuser.is_staff}")
        print(f"Superuser has superuser status: {self.superuser.is_superuser}")
        print(f"Inspector has staff status: {self.inspector_user.is_staff}")
        print(f"Inspector can view teachers: {bool(self.inspector.view_teachers())}")
        print(f"Regular user has staff status: {self.regular_user.is_staff}")
        print(f"Regular user has superuser status: {self.regular_user.is_superuser}")

        print("\nTest 4: Verify Inspector functionality")
        # Test that inspector can view teachers
        teachers = self.inspector.view_teachers()
        print("\nTest 4: Verify Inspector functionality")
        # Test that inspector can view teachers
        teachers = self.inspector.view_teachers()
        print(f"Inspector can see {teachers.count()} teachers")

        # Test that inspector can view students
        students = self.inspector.view_students()
        print(f"Inspector can see {students.count()}  students")

