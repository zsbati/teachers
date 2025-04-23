from django.contrib import admin
from .models import Teacher, Inspector, Student, Task, WorkSession, SuperUser, CustomUser
from .billing_models import Bill, BillItem
from decimal import Decimal

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'hourly_rate', 'description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    
    def get_changeform_initial_data(self, request):
        # Set default hourly rate if not provided
        return {'hourly_rate': Decimal('15.00')}  # Default rate of $15/hour

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_teacher', 'is_inspector', 'is_superuser')
    list_filter = ('is_teacher', 'is_inspector', 'is_superuser')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'subjects')
    search_fields = ('user__username', 'subjects')

@admin.register(Inspector)
class InspectorAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_login')
    search_fields = ('user__username',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ('get_username','get_email','phone','is_active')
    search_fields = ('user__username','user__email','phone')
    list_filter = ('is_active',)

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'task', 'entry_type', 'created_at', 'total_amount')
    list_filter = ('entry_type', 'created_at', 'task')
    search_fields = ('teacher__user__username', 'task__name')

@admin.register(SuperUser)
class SuperUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_login')
    search_fields = ('user__username',)

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'month')
    search_fields = ('student__user__username', 'student__user__email')
    date_hierarchy = 'month'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('student__user')

@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ('bill', 'service_name', 'quantity', 'amount')
    list_filter = ('bill__month',)
    search_fields = ('service_name', 'bill__student__user__username')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('bill', 'bill__student__user')
