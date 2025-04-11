from django.db import models
from django.contrib.auth.models import AbstractUser


# Custom User Model
class CustomUser(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_inspector = models.BooleanField(default=False)


# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.user.username


# Inspector Model
class Inspector(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


# Student Model
class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name
