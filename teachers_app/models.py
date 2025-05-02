from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from datetime import datetime


# Custom User Model
class CustomUser(AbstractUser):
    is_student   = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_inspector = models.BooleanField(default=False)
    #  is_superuser = models.BooleanField(default=False)

    @property
    def is_inspector_effective(self):
        return self.is_superuser or self.is_inspector

# Teacher Model (simplified - only user association)
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    subjects = models.CharField(max_length=200, blank=True, help_text="Optional: List of subjects taught")

    def __str__(self):
        return f"{self.user.username} - {self.subjects}" if self.subjects else self.user.username

# Student model using current AUTH_USER_MODEL (profile)
class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

# Task Model (different types of work with their rates)
class Task(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.DurationField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
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
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Store the hourly rate at creation time
    stored_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Store the hours at creation time
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    student = models.ForeignKey(
    Student,
    on_delete=models.SET_NULL,
    null=True,    # Makes it nullable in the DB
    blank=True    # Allows blank in forms
)
    # For manual entry
    manual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # For clock in/out
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)

    # For time range entry
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Student billing amount
    teacher_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Teacher's payment amount

    def save(self, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("=== WorkSession save method started ===")
        logger.debug(f"Initial state: hourly_rate={self.hourly_rate}, stored_hours={self.stored_hours}, task={self.task}")
        logger.debug(f"Task price: {self.task.price}, Task hourly_rate: {self.task.hourly_rate}")
        
        # Store the hourly rate at creation time if it's a new record
        if not self.pk:  # Only set on creation
            logger.debug("New record - setting hourly rate from task")
            self.hourly_rate = self.task.hourly_rate
            logger.debug(f"Task hourly rate set to: {self.hourly_rate}")
        
        # Store hours based on entry type
        logger.debug(f"Entry type: {self.entry_type}")
        if self.entry_type == 'manual':
            if self.manual_hours is not None:
                self.stored_hours = self.manual_hours
                logger.debug(f"Manual hours set to: {self.stored_hours}")
            else:
                raise ValueError("Manual entry type requires manual_hours")
        elif self.entry_type == 'clock':
            # For clock entry type, we only calculate hours when clocking out
            if self.clock_in and self.clock_out:
                hours = (self.clock_out - self.clock_in).total_seconds() / 3600
                # Round clock-in/out hours to nearest hour
                self.stored_hours = Decimal(str(hours)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                logger.debug(f"Clock hours calculated: {self.stored_hours}")
            # When clocking in, just set clock_in and don't calculate hours yet
            elif self.clock_in and not self.clock_out:
                logger.debug("Clocking in - storing clock_in time only")
            else:
                raise ValueError("Clock entry type requires clock_in")
        elif self.entry_type == 'time_range':
            if self.start_time and self.end_time:
                duration = self.end_time - self.start_time
                hours = Decimal(str(duration.total_seconds() / 3600))
                # Round time-range hours to nearest hour
                self.stored_hours = hours.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                logger.debug(f"Time range hours calculated: {self.stored_hours}")
            else:
                raise ValueError("Time range entry type requires start_time and end_time")
        
        # Calculate amounts for both student and teacher
        logger.debug(f"Final hourly rate: {self.hourly_rate}")
        logger.debug(f"Final stored hours: {self.stored_hours}")
        logger.debug(f"Task price: {self.task.price}, Task hourly_rate: {self.task.hourly_rate}")
        
        # Only calculate amounts if we have stored hours (which means we've clocked out)
        if self.stored_hours is not None and self.stored_hours > 0:
            # Calculate student billing amount (0 for free tasks)
            if self.task.price == 0 or self.task.price == Decimal('0.00'):
                logger.debug("Free task for student - setting student total_amount to 0")
                self.total_amount = Decimal('0.00')
            else:
                # Calculate total amount for paid tasks (student billing)
                self.total_amount = self.stored_hours * self.task.price  # Use hourly_rate for student billing
                logger.debug(f"Calculated student total amount: {self.total_amount}")
            
            # Calculate teacher payment amount (always based on hourly_rate)
            if self.hourly_rate is not None:
                self.teacher_payment_amount = self.stored_hours * self.hourly_rate
                logger.debug(f"Calculated teacher payment amount: {self.teacher_payment_amount}")
        else:
            logger.debug("Not calculating amounts - either no hours stored or hours not positive")
            self.total_amount = None
            self.teacher_payment_amount = None
        
        super().save(*args, **kwargs)
        logger.debug("=== WorkSession save method completed ===")

    def clean(self):
        """Validate the entry type requirements"""
        if self.entry_type == 'manual' and not self.manual_hours:
            raise ValidationError({
                'manual_hours': 'Manual entry type requires manual_hours'
            })
        elif self.entry_type == 'clock':
            if not self.clock_in or not self.clock_out:
                raise ValidationError({
                    'clock_in': 'Clock entry type requires both clock_in and clock_out',
                    'clock_out': 'Clock entry type requires both clock_in and clock_out'
                })
            if self.clock_in >= self.clock_out:
                raise ValidationError({
                    'clock_out': 'Clock out must be after clock in'
                })
        elif self.entry_type == 'time_range':
            if not self.start_time or not self.end_time:
                raise ValidationError({
                    'start_time': 'Time range entry type requires both start_time and end_time',
                    'end_time': 'Time range entry type requires both start_time and end_time'
                })
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': 'End time must be after start time'
                })

    @property
    def calculated_hours(self):
        """Return stored hours"""
        return self.stored_hours or Decimal(0)

    @property
    def calculated_amount(self):
        """Calculate amount using stored values"""
        if self.stored_hours and self.hourly_rate:
            return self.stored_hours * self.hourly_rate
        return None

    def calculated_hours(self):
        """
        Calculate the total hours worked based on the entry type.
        - Manual: Use `manual_hours`.
        - Clock: Use `clock_in` and `clock_out`.
        - Time Range: Use `start_time` and `end_time`.
        """
        if self.entry_type == 'manual' and self.manual_hours:
            return self.manual_hours
        elif self.entry_type == 'clock' and self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            return duration.total_seconds() / 3600  # Return hours
        elif self.entry_type == 'time_range' and self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() / 3600  # Return hours
        return None  # Return None if no valid data

    def __str__(self):
        if self.entry_type == 'manual':
            return f"{self.teacher} - {self.task} - {self.manual_hours} hours"
        elif self.entry_type == 'time_range':
            return f"{self.teacher} - {self.task} - {self.start_time} to {self.end_time}"
        return f"{self.teacher} - {self.task} - {self.clock_in} to {self.clock_out}"




# Inspector Model (Base class with view-only privileges)
class Inspector(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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

    def create_salary_report(self, teacher_id, year, month, notes=""):
        """Create a salary report for a teacher for a specific month"""
        teacher = Teacher.objects.get(id=teacher_id)
        return SalaryReport.create_for_month(
            teacher=teacher,
            year=year,
            month=month,
            created_by=self.user,
            notes=notes
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


# Service Model
class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (${self.price})"

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

# Salary Report Model
class SalaryReport(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Salary Report - {self.teacher} ({self.start_date.strftime('%B %Y')})"

    @classmethod
    def create_for_month(cls, teacher, year, month, created_by, notes=""):
        """Create a salary report for a specific month with historical data"""
        start_date = timezone.make_aware(datetime(year, month, 1))
        end_date = timezone.make_aware(datetime(year, month + 1, 1)) if month < 12 else \
                   timezone.make_aware(datetime(year + 1, 1, 1))

        # Get all work sessions for this month
        work_sessions = WorkSession.objects.filter(
            teacher=teacher,
            created_at__gte=start_date,
            created_at__lt=end_date,
            is_deleted=False
        )

        # Calculate total hours and amount using stored values
        total_hours = Decimal(0)
        total_amount = Decimal(0)
        
        for session in work_sessions:
            if session.stored_hours and session.hourly_rate:
                total_hours += session.stored_hours
                total_amount += session.stored_hours * session.hourly_rate

        # Create the report with historical data
        report = cls.objects.create(
            teacher=teacher,
            start_date=start_date,
            end_date=end_date,
            total_hours=total_hours,
            total_amount=total_amount,
            created_by=created_by,
            notes=notes
        )
        return report

    def delete(self, *args, **kwargs):
        """Soft delete the report"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def get_work_sessions(self):
        """Get all work sessions for this report"""
        return WorkSession.objects.filter(
            teacher=self.teacher,
            created_at__gte=self.start_date,
            created_at__lt=self.end_date,
            is_deleted=False
        )