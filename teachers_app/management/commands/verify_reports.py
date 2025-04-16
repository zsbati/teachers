from django.core.management.base import BaseCommand
from teachers_app.models import SalaryReport, WorkSession
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Verify salary reports and their calculations'

    def handle(self, *args, **options):
        reports = SalaryReport.objects.all()
        
        self.stdout.write(self.style.SUCCESS('Verifying Salary Reports:'))
        
        for report in reports:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(f"Report for {report.teacher} ({report.start_date.strftime('%B %Y')})")
            self.stdout.write(f"Total Hours: {report.total_hours}")
            self.stdout.write(f"Total Amount: {report.total_amount}")
            
            work_sessions = WorkSession.objects.filter(
                teacher=report.teacher,
                created_at__gte=report.start_date,
                created_at__lt=report.end_date
            )
            
            calculated_hours = Decimal(0)
            calculated_amount = Decimal(0)
            
            self.stdout.write("\nWork Sessions:")
            for session in work_sessions:
                hours = Decimal(0)
                if session.entry_type == 'manual' and session.manual_hours:
                    hours = session.manual_hours
                elif session.entry_type == 'clock' and session.clock_in and session.clock_out:
                    duration = session.clock_out - session.clock_in
                    hours = Decimal(str(duration.total_seconds() / 3600))
                elif session.entry_type == 'time_range' and session.start_time and session.end_time:
                    duration = session.end_time - session.start_time
                    hours = Decimal(str(duration.total_seconds() / 3600))
                
                calculated_hours += hours
                calculated_amount += session.total_amount
                
                self.stdout.write(f"  - Session: {session.entry_type}")
                self.stdout.write(f"    Hours: {hours}")
                self.stdout.write(f"    Amount: {session.total_amount}")
            
            self.stdout.write("\nCalculated Totals:")
            self.stdout.write(f"Total Hours (stored): {report.total_hours}")
            self.stdout.write(f"Total Hours (calculated): {calculated_hours}")
            self.stdout.write(f"Total Amount (stored): {report.total_amount}")
            self.stdout.write(f"Total Amount (calculated): {calculated_amount}")
            self.stdout.write('=' * 50)
