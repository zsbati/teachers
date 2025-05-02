from decimal import Decimal, ROUND_HALF_UP
import django.utils.timezone as timezone
from datetime import datetime, timedelta
from .models import Teacher, Task, WorkSession, Student


class SalaryCalculationService:
    @staticmethod
    def calculate_salary(teacher, year, month):
        """Calculate salary details for a teacher in a specific month"""
        # Calculate start and end dates for the month with timezone awareness
        start_date = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(year, month + 1, 1))
        end_date = end_date - timedelta(microseconds=1)

        work_sessions = WorkSession.objects.filter(
            teacher=teacher,
            created_at__gte=start_date,
            created_at__lte=end_date,
            is_deleted=False
        ).select_related('task')

        total = Decimal('0.00')
        task_summaries = []
        session_details = []

        for session in work_sessions:
            hours = session.stored_hours or Decimal('0.00')
            rate = session.hourly_rate or Decimal('0.00')
            task_total = (hours * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            rounded_hours = hours.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total += task_total

            task_summaries.append({
                'task_name': session.task.name,
                'hours': str(rounded_hours),  # Use string for display, keep Decimal for calculations
                'rate': str(rate),
                'student': getattr(session.student, 'name', None) if getattr(session, 'student', None) else None,
                'total': str(task_total)
            })

            session_details.append({
                'date': session.created_at,
                'task': session.task.name,
                'hours': str(rounded_hours),
                'rate': str(rate),
                'amount': str(task_total),
                'entry_type': session.get_entry_type_display(),
                'notes': session.task.description if session.task.description else ''
            })

        return {
            'task_summaries': task_summaries,
            'session_details': sorted(session_details, key=lambda x: x['date']),
            'total_salary': str(total),
            'period': f"{start_date.strftime('%B %Y')}"
        }
