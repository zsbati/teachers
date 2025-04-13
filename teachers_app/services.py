from decimal import Decimal
from django.utils import timezone
from .models import Teacher, Task, WorkSession

class SalaryCalculationService:
    @staticmethod
    def calculate_salary(teacher, year, month):
        """Calculate salary details for a teacher in a specific month"""
        # Calculate start and end dates for the month
        start_date = timezone.datetime(year, month, 1)
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1)
        else:
            end_date = timezone.datetime(year, month + 1, 1)
        end_date = end_date - timezone.timedelta(microseconds=1)

        # Get work sessions for the period
        work_sessions = WorkSession.objects.filter(
            teacher=teacher,
            created_at__range=(start_date, end_date)
        ).order_by('created_at')
        
        task_summaries = []
        session_details = []
        total = Decimal('0.00')
        
        # Group work sessions by task
        for task in Task.objects.filter(worksession__in=work_sessions).distinct():
            task_sessions = work_sessions.filter(task=task)
            total_hours = Decimal('0.00')
            for session in task_sessions:
                hours = session.calculated_hours or 0
                total_hours += Decimal(str(hours))
            
            task_total = task.hourly_rate * total_hours
            total += task_total
            
            task_summaries.append({
                'task_name': task.name,
                'hours': float(total_hours),  # Convert to float for template display
                'rate': task.hourly_rate,
                'total': task_total
            })
            
            # Add individual session details for this task
            for session in task_sessions:
                hours = Decimal(str(session.calculated_hours or 0))
                session_details.append({
                    'date': session.created_at.date(),
                    'task_name': task.name,
                    'hours': float(hours),  # Convert to float for template display
                    'rate': task.hourly_rate,
                    'total': hours * task.hourly_rate,
                    'entry_type': session.get_entry_type_display(),
                    'notes': f"{session}"
                })
        
        return {
            'task_summaries': task_summaries,
            'session_details': sorted(session_details, key=lambda x: x['date']),
            'total_salary': total,
            'period': f"{start_date.strftime('%B %Y')}"
        }
