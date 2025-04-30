from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from teachers_app.models import CustomUser, Teacher, Student, Inspector
from django.db.models import Q
import sys

class Command(BaseCommand):
    help = 'Verify user roles and permissions'

    def handle(self, *args, **options):
        users = CustomUser.objects.all()
        has_errors = False
        
        self.stdout.write("\nVerifying User Roles:")
        
        for user in users:
            self.stdout.write(f"\nUser {user.username}:")
            
            # Check role consistency
            roles = sum([user.is_student, user.is_teacher, user.is_inspector])
            if roles > 1:
                self.stdout.write(self.style.ERROR("User has multiple roles assigned"))
                has_errors = True
            elif roles == 0 and not user.is_superuser:
                self.stdout.write(self.style.ERROR("User has no role assigned"))
                has_errors = True
            
            # Check related models
            if user.is_student:
                if not hasattr(user, 'student'):
                    self.stdout.write(self.style.ERROR("Student user has no Student profile"))
                    has_errors = True
            
            if user.is_teacher:
                if not hasattr(user, 'teacher'):
                    self.stdout.write(self.style.ERROR("Teacher user has no Teacher profile"))
                    has_errors = True
            
            if user.is_inspector:
                if not hasattr(user, 'inspector'):
                    self.stdout.write(self.style.ERROR("Inspector user has no Inspector profile"))
                    has_errors = True
            
            # Check permissions
            if user.is_inspector:
                if not user.has_perm('teachers_app.view_teachers'):
                    self.stdout.write(self.style.ERROR("Inspector lacks view_teachers permission"))
                    has_errors = True
            
            if user.is_superuser:
                if not user.is_staff:
                    self.stdout.write(self.style.ERROR("Superuser is not staff"))
                    has_errors = True
            
            # Check orphaned profiles
            if hasattr(user, 'teacher') and not user.is_teacher:
                self.stdout.write(self.style.ERROR("Teacher profile exists but user is not marked as teacher"))
                has_errors = True
            
            if hasattr(user, 'student') and not user.is_student:
                self.stdout.write(self.style.ERROR("Student profile exists but user is not marked as student"))
                has_errors = True
            
            if hasattr(user, 'inspector') and not user.is_inspector:
                self.stdout.write(self.style.ERROR("Inspector profile exists but user is not marked as inspector"))
                has_errors = True
            
            if not has_errors:
                self.stdout.write(self.style.SUCCESS("User roles are valid"))
        
        # Check for orphaned profiles
        orphaned_teachers = Teacher.objects.filter(user__is_teacher=False)
        if orphaned_teachers.exists():
            self.stdout.write(self.style.ERROR("\nOrphaned Teacher profiles:"))
            for teacher in orphaned_teachers:
                self.stdout.write(f"  {teacher}")
            has_errors = True
        
        orphaned_students = Student.objects.filter(user__is_student=False)
        if orphaned_students.exists():
            self.stdout.write(self.style.ERROR("\nOrphaned Student profiles:"))
            for student in orphaned_students:
                self.stdout.write(f"  {student}")
            has_errors = True
        
        orphaned_inspectors = Inspector.objects.filter(user__is_inspector=False)
        if orphaned_inspectors.exists():
            self.stdout.write(self.style.ERROR("\nOrphaned Inspector profiles:"))
            for inspector in orphaned_inspectors:
                self.stdout.write(f"  {inspector}")
            has_errors = True
        
        if has_errors:
            self.stdout.write(self.style.ERROR("\nERROR: Some user roles have issues!"))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\nAll user roles are valid!"))
