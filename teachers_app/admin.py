from django.contrib import admin
from .models import Teacher, Inspector, Student, Task, WorkSession, SuperUser, CustomUser

admin.site.register(CustomUser)
admin.site.register(Teacher)
admin.site.register(Inspector)
admin.site.register(Student)
admin.site.register(Task)
admin.site.register(WorkSession)
admin.site.register(SuperUser)
