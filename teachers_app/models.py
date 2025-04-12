from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.contenttypes.models import ContentType


# Custom User Model
class CustomUser(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_inspector = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)


# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.user.username


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

    def add_teacher(self, username, password, subject, hourly_rate):
        """Add a new teacher"""
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            is_teacher=True
        )
        return Teacher.objects.create(
            user=user,
            subject=subject,
            hourly_rate=hourly_rate
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


# Student Model
class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name
