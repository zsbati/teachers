from django.core.management.base import BaseCommand
from teachers_app.models import SalaryReport, WorkSession
from django.utils import timezone
from decimal import Decimal
import sys

class Command(BaseCommand):
    help = 'Verify salary reports against their work sessions'

    def handle(self, *args, **options):
        # Get all salary reports
        reports = SalaryReport.objects.filter(is_deleted=False)
        
        has_errors = False
        
        self.stdout.write("\nVerifying Salary Reports:")
        
        for report in reports:
            self.stdout.write(f"\nReport for {report.teacher} ({report.start_date.strftime('%B %Y')}):")
            self.stdout.write(f"Reported Hours: {report.total_hours}")
            self.stdout.write(f"Reported Amount: {report.total_amount}")
            
            # Get associated work sessions
            work_sessions = WorkSession.objects.filter(
                teacher=report.teacher,
                created_at__gte=report.start_date,
                created_at__lt=report.end_date,
                is_deleted=False
            )
            
            # Calculate actual totals
            actual_hours = Decimal(0)
            actual_amount = Decimal(0)
            
            for session in work_sessions:
                if session.stored_hours and session.hourly_rate:
                    actual_hours += session.stored_hours
                    actual_amount += session.stored_hours * session.hourly_rate
            
            # Verify the calculations
            hours_match = report.total_hours == actual_hours
            amount_match = report.total_amount == actual_amount
            
            self.stdout.write(f"Actual Hours: {actual_hours}")
            self.stdout.write(f"Actual Amount: {actual_amount}")
            
            if not hours_match or not amount_match:
                has_errors = True
                self.stdout.write(self.style.ERROR("MISMATCH DETECTED:"))
                if not hours_match:
                    self.stdout.write(self.style.ERROR(f"  Hours mismatch: {report.total_hours} != {actual_hours}"))
                if not amount_match:
                    self.stdout.write(self.style.ERROR(f"  Amount mismatch: {report.total_amount} != {actual_amount}"))
            else:
                self.stdout.write(self.style.SUCCESS("Calculations match!"))
            
            # List work sessions if there's a mismatch
            if not hours_match or not amount_match:
                self.stdout.write("\nWork Sessions:")
                for session in work_sessions:
                    self.stdout.write(f"  - {session.task.name}")
                    self.stdout.write(f"    Hours: {session.stored_hours}")
                    self.stdout.write(f"    Rate: ${session.hourly_rate}")
                    self.stdout.write(f"    Amount: ${session.stored_hours * session.hourly_rate}")
        
        if has_errors:
            self.stdout.write(self.style.ERROR("\nERROR: Some salary reports have calculation mismatches!"))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\nAll salary reports verified successfully!"))
