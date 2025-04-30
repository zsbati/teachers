from django.core.management.base import BaseCommand
from django.db import models
from teachers_app.models import CustomUser, Teacher, Student, Inspector, WorkSession, Task
from teachers_app.billing_models import Bill, BillItem
from django.db.models import Count, Q
import sys

class Command(BaseCommand):
    help = 'Verify database integrity and relationships'

    def handle(self, *args, **options):
        has_errors = False
        
        self.stdout.write("\nVerifying Database Integrity:")
        
        # Check for orphaned records
        self.stdout.write("\nChecking for orphaned records:")
        
        # Teachers without users
        orphaned_teachers = Teacher.objects.filter(user__isnull=True)
        if orphaned_teachers.exists():
            self.stdout.write(self.style.ERROR("Orphaned Teachers:"))
            for teacher in orphaned_teachers:
                self.stdout.write(f"  {teacher}")
            has_errors = True
        
        # Students without users
        orphaned_students = Student.objects.filter(user__isnull=True)
        if orphaned_students.exists():
            self.stdout.write(self.style.ERROR("Orphaned Students:"))
            for student in orphaned_students:
                self.stdout.write(f"  {student}")
            has_errors = True
        
        # Inspectors without users
        orphaned_inspectors = Inspector.objects.filter(user__isnull=True)
        if orphaned_inspectors.exists():
            self.stdout.write(self.style.ERROR("Orphaned Inspectors:"))
            for inspector in orphaned_inspectors:
                self.stdout.write(f"  {inspector}")
            has_errors = True
        
        # Work sessions without teachers
        orphaned_sessions = WorkSession.objects.filter(teacher__isnull=True)
        if orphaned_sessions.exists():
            self.stdout.write(self.style.ERROR("Work Sessions without Teachers:"))
            for session in orphaned_sessions:
                self.stdout.write(f"  Session {session.id}")
            has_errors = True
        
        # Work sessions without tasks
        orphaned_sessions = WorkSession.objects.filter(task__isnull=True)
        if orphaned_sessions.exists():
            self.stdout.write(self.style.ERROR("Work Sessions without Tasks:"))
            for session in orphaned_sessions:
                self.stdout.write(f"  Session {session.id}")
            has_errors = True
        
        # Bills without students
        orphaned_bills = Bill.objects.filter(student__isnull=True)
        if orphaned_bills.exists():
            self.stdout.write(self.style.ERROR("Bills without Students:"))
            for bill in orphaned_bills:
                self.stdout.write(f"  Bill {bill.id}")
            has_errors = True
        
        # Bill items without bills
        orphaned_items = BillItem.objects.filter(bill__isnull=True)
        if orphaned_items.exists():
            self.stdout.write(self.style.ERROR("Bill Items without Bills:"))
            for item in orphaned_items:
                self.stdout.write(f"  Item {item.id}")
            has_errors = True
        
        # Check for duplicate records
        self.stdout.write("\nChecking for duplicates:")
        
        # Duplicate teachers for same user
        duplicate_teachers = CustomUser.objects.annotate(
            teacher_count=Count('teacher')
        ).filter(teacher_count__gt=1)
        if duplicate_teachers.exists():
            self.stdout.write(self.style.ERROR("Users with multiple Teacher profiles:"))
            for user in duplicate_teachers:
                self.stdout.write(f"  {user.username}")
            has_errors = True
        
        # Duplicate students for same user
        duplicate_students = CustomUser.objects.annotate(
            student_count=Count('student')
        ).filter(student_count__gt=1)
        if duplicate_students.exists():
            self.stdout.write(self.style.ERROR("Users with multiple Student profiles:"))
            for user in duplicate_students:
                self.stdout.write(f"  {user.username}")
            has_errors = True
        
        # Duplicate inspectors for same user
        duplicate_inspectors = CustomUser.objects.annotate(
            inspector_count=Count('inspector')
        ).filter(inspector_count__gt=1)
        if duplicate_inspectors.exists():
            self.stdout.write(self.style.ERROR("Users with multiple Inspector profiles:"))
            for user in duplicate_inspectors:
                self.stdout.write(f"  {user.username}")
            has_errors = True
        
        # Check for incomplete records
        self.stdout.write("\nChecking for incomplete records:")
        
        # Tasks without hourly rates
        tasks_without_rates = Task.objects.filter(hourly_rate__isnull=True)
        if tasks_without_rates.exists():
            self.stdout.write(self.style.ERROR("Tasks without hourly rates:"))
            for task in tasks_without_rates:
                self.stdout.write(f"  {task.name}")
            has_errors = True
        
        # Work sessions without hourly rates
        sessions_without_rates = WorkSession.objects.filter(hourly_rate__isnull=True)
        if sessions_without_rates.exists():
            self.stdout.write(self.style.ERROR("Work Sessions without hourly rates:"))
            for session in sessions_without_rates:
                self.stdout.write(f"  Session {session.id}")
            has_errors = True
        
        # Work sessions without stored hours
        sessions_without_hours = WorkSession.objects.filter(stored_hours__isnull=True)
        if sessions_without_hours.exists():
            self.stdout.write(self.style.ERROR("Work Sessions without stored hours:"))
            for session in sessions_without_hours:
                self.stdout.write(f"  Session {session.id}")
            has_errors = True
        
        # Bills without total amounts
        bills_without_amounts = Bill.objects.filter(total_amount__isnull=True)
        if bills_without_amounts.exists():
            self.stdout.write(self.style.ERROR("Bills without total amounts:"))
            for bill in bills_without_amounts:
                self.stdout.write(f"  Bill {bill.id}")
            has_errors = True
        
        if has_errors:
            self.stdout.write(self.style.ERROR("\nERROR: Database integrity issues found!"))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\nDatabase integrity verified successfully!"))
