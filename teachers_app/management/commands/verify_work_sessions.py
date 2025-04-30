from django.core.management.base import BaseCommand
from teachers_app.models import WorkSession
from django.utils import timezone
from datetime import timedelta
import sys

class Command(BaseCommand):
    help = 'Verify work session consistency and integrity'

    def handle(self, *args, **options):
        sessions = WorkSession.objects.filter(is_deleted=False)
        has_errors = False
        
        self.stdout.write("\nVerifying Work Sessions:")
        
        for session in sessions:
            self.stdout.write(f"\nSession {session.id} - {session.teacher}")
            
            # Check entry type consistency
            if session.entry_type == 'clock':
                if not session.clock_in or not session.clock_out:
                    self.stdout.write(self.style.ERROR("Clock session missing clock_in or clock_out"))
                    has_errors = True
                elif session.clock_in >= session.clock_out:
                    self.stdout.write(self.style.ERROR("Clock out is not after clock in"))
                    has_errors = True
            
            elif session.entry_type == 'time_range':
                if not session.start_time or not session.end_time:
                    self.stdout.write(self.style.ERROR("Time range session missing start_time or end_time"))
                    has_errors = True
                elif session.start_time >= session.end_time:
                    self.stdout.write(self.style.ERROR("End time is not after start time"))
                    has_errors = True
            
            # Check hours calculation
            if session.stored_hours is None:
                self.stdout.write(self.style.ERROR("Stored hours is None"))
                has_errors = True
            
            # Check hourly rate
            if session.hourly_rate is None:
                self.stdout.write(self.style.ERROR("Hourly rate is None"))
                has_errors = True
            
            # Check total amount calculation
            if session.total_amount is None:
                self.stdout.write(self.style.ERROR("Total amount is None"))
                has_errors = True
            elif session.total_amount != session.stored_hours * session.hourly_rate:
                self.stdout.write(self.style.ERROR("Total amount doesn't match hours * rate"))
                has_errors = True
            
            # Check for overlapping sessions
            # Convert Decimal hours to float for timedelta
            hours_float = float(session.stored_hours)
            # Check for overlapping sessions
            # Get all sessions within a reasonable time window
            potential_overlaps = WorkSession.objects.filter(
                teacher=session.teacher,
                is_deleted=False,
                created_at__lt=session.created_at + timedelta(hours=hours_float + 1),
                created_at__gt=session.created_at - timedelta(hours=hours_float + 1)
            ).exclude(id=session.id)

            # Check for actual overlaps
            overlapping = []
            for other_session in potential_overlaps:
                # Get the time ranges for both sessions
                session_range = {
                    'start': session.created_at,
                    'end': session.created_at + timedelta(hours=hours_float)
                }
                other_range = {
                    'start': other_session.created_at,
                    'end': other_session.created_at + timedelta(hours=float(other_session.stored_hours))
                }

                # Check if ranges overlap
                if (session_range['start'] < other_range['end'] and 
                    session_range['end'] > other_range['start']):
                    overlapping.append(other_session)
            
            if overlapping:
                self.stdout.write(self.style.ERROR("Overlapping sessions detected"))
                self.stdout.write(self.style.ERROR("Detailed overlap information:"))
                for overlap in overlapping:
                    self.stdout.write(f"  Overlaps with session {overlap.id}:")
                    self.stdout.write(f"    This session: {session.created_at} to {session.created_at + timedelta(hours=hours_float)}")
                    self.stdout.write(f"    Other session: {overlap.created_at} to {overlap.created_at + timedelta(hours=float(overlap.stored_hours))}")
                has_errors = True
            
            if not has_errors:
                self.stdout.write(self.style.SUCCESS("Session is valid"))
        
        if has_errors:
            self.stdout.write(self.style.ERROR("\nERROR: Some work sessions have issues!"))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\nAll work sessions are valid!"))
