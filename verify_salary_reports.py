from teachers_app.models import SalaryReport, WorkSession
from django.utils import timezone

# Get all salary reports with their calculated values
reports = SalaryReport.objects.all()

print("\nVerifying Salary Reports:")
for report in reports:
    print(f"\nReport for {report.teacher} ({report.start_date.strftime('%B %Y')}):")
    print(f"Total Hours: {report.total_hours}")
    print(f"Total Amount: {report.total_amount}")
    
    # Get associated work sessions to verify the calculation
    work_sessions = WorkSession.objects.filter(
        teacher=report.teacher,
        created_at__gte=report.start_date,
        created_at__lt=report.end_date
    )
    
    calculated_hours = Decimal(0)
    calculated_amount = Decimal(0)
    
    print("\nWork Sessions:")
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
        
        print(f"  - Session: {session.entry_type}")
        print(f"    Hours: {hours}")
        print(f"    Amount: {session.total_amount}")
    
    print(f"\nCalculated Totals:")
    print(f"Total Hours (stored): {report.total_hours}")
    print(f"Total Hours (calculated): {calculated_hours}")
    print(f"Total Amount (stored): {report.total_amount}")
    print(f"Total Amount (calculated): {calculated_amount}")
    print("-" * 50)
