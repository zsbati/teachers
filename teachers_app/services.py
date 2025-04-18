from decimal import Decimal, ROUND_HALF_UP
import django.utils.timezone as timezone
from .models import Teacher, Task, WorkSession


class SalaryCalculationService:
    @staticmethod
    def calculate_salary(teacher, year, month):
        """Calculate salary details for a teacher in a specific month"""
        # Calculate start and end dates for the month with timezone awareness
        start_date = timezone.make_aware(timezone.datetime(year, month, 1))
        if month == 12:
            end_date = timezone.make_aware(timezone.datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(timezone.datetime(year, month + 1, 1))
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
                hours = session.calculated_hours()
                
                print(f"Session ID: {getattr(session, 'id', 'N/A')}, entry_type: {getattr(session, 'entry_type', 'N/A')}, calculated_hours: {hours}")
                if hours is not None:
                    try:
                        # Round hours to nearest hour for clock and time_range entries
                        if session.entry_type in ['clock', 'time_range']:
                            hours_decimal = Decimal(str(hours)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                        else:
                            hours_decimal = Decimal(str(hours))
                    except Exception as e:
                        print(f"Invalid value for hours: {hours} (Session ID: {getattr(session, 'id', 'N/A')}) - Error: {e}")
                        continue  # Skip this session if conversion fails

                    total_hours += hours_decimal
                    session_total = hours_decimal * (session.hourly_rate if session.hourly_rate is not None else task.hourly_rate)

                    session_details.append({
                        'date': session.created_at.date(),
                        'time': (
                            f"{session.clock_in.strftime('%H:%M')} - {session.clock_out.strftime('%H:%M')}"
                            if session.entry_type == 'clock' and session.clock_in and session.clock_out
                            else (
                                f"{session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}"
                                if session.entry_type == 'time_range' and session.start_time and session.end_time
                                else ''
                            )
                        ),
                        'task_name': task.name,
                        'hours': float(hours_decimal),
                        'rate': session.hourly_rate if session.hourly_rate is not None else task.hourly_rate,
                        'total': session_total,
                        'entry_type': session.entry_type,
                        'notes': f"{session}"
                    })

            # Round total_hours to nearest hour for clock/time_range entries
            rounded_hours = total_hours
            if any(s.entry_type in ['clock', 'time_range'] for s in task_sessions):
                rounded_hours = total_hours.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            task_total = task.hourly_rate * rounded_hours
            total += task_total

            task_summaries.append({
                'task_name': task.name,
                'hours': float(rounded_hours),
                'rate': task.hourly_rate,
                'total': task_total
            })

        return {
            'task_summaries': task_summaries,
            'session_details': sorted(session_details, key=lambda x: x['date']),
            'total_salary': total,
            'period': f"{start_date.strftime('%B %Y')}"
        }
