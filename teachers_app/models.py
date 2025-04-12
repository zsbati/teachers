from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal


# Custom User Model
class CustomUser(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_inspector = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)


# Teacher Model (simplified - only user association)
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    subjects = models.CharField(max_length=200, blank=True, help_text="Optional: List of subjects taught")

    def __str__(self):
        return f"{self.user.username} - {self.subjects}" if self.subjects else self.user.username


# Task Model (different types of work with their rates)
class Task(models.Model):
    name = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (${self.hourly_rate}/hour)"


# Work Session Model
class WorkSession(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('manual', 'Manual Hours Input'),
        ('clock', 'Clock In/Out'),
        ('time_range', 'Time Range'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)

    # For manual entry
    manual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # For clock in/out
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)

    # For time range entry
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Calculate total amount based on entry type
        if self.entry_type == 'manual' and self.manual_hours:
            self.total_amount = self.task.hourly_rate * self.manual_hours
        elif self.entry_type == 'clock' and self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            hours = Decimal(str(duration.total_seconds() / 3600))  # Convert to Decimal
            self.total_amount = self.task.hourly_rate * hours
        elif self.entry_type == 'time_range' and self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            hours = Decimal(str(duration.total_seconds() / 3600))  # Convert to Decimal
            self.total_amount = self.task.hourly_rate * hours
        super().save(*args, **kwargs)

    def __str__(self):
        if self.entry_type == 'manual':
            return f"{self.teacher} - {self.task} - {self.manual_hours} hours"
        elif self.entry_type == 'time_range':
            return f"{self.teacher} - {self.task} - {self.start_time} to {self.end_time}"
        return f"{self.teacher} - {self.task} - {self.clock_in} to {self.clock_out}"


# Student Model
class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name


# Inspector Model (Base class with view-only privileges)
class Inspector(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inspector: {self.user.username}"

    def change_own_password(self, new_password):
        """Only method that inspectors can use to modify data - changing their own password"""
        if self.user:
            self.user.set_password(new_password)
            self.user.save()

    def view_teachers(self):
        """View all teachers"""
        return Teacher.objects.all()

    def view_students(self):
        """View all students"""
        return Student.objects.all()


# SuperUser Model (Extends Inspector with full privileges)
class SuperUser(Inspector):
    class Meta:
        verbose_name = 'Super User'
        verbose_name_plural = 'Super Users'

    def add_teacher(self, username, password, subjects=None):
        """Add a new teacher"""
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            is_teacher=True
        )
        return Teacher.objects.create(
            user=user,
            subjects=subjects or ""
        )

    def remove_teacher(self, teacher_id):
        """Remove a teacher"""
        teacher = Teacher.objects.get(id=teacher_id)
        user = teacher.user
        teacher.delete()
        user.delete()

    def add_student(self, name, email):
        """Add a new student"""
        return Student.objects.create(
            name=name,
            email=email
        )

    def remove_student(self, student_id):
        """Remove a student"""
        Student.objects.get(id=student_id).delete()

    def change_user_password(self, user_id, new_password):
        """Change password for any user"""
        user = CustomUser.objects.get(id=user_id)
        user.set_password(new_password)
        user.save()
