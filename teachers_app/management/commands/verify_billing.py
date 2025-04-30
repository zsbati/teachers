from django.core.management.base import BaseCommand
from teachers_app.models import Student
from teachers_app.billing_models import Bill, BillItem
from decimal import Decimal
import sys

class Command(BaseCommand):
    help = 'Verify billing consistency and integrity'

    def handle(self, *args, **options):
        bills = Bill.objects.all()
        has_errors = False
        
        self.stdout.write("\nVerifying Bills:")
        
        for bill in bills:
            self.stdout.write(f"\nBill {bill.id} - {bill.student} ({bill.month.strftime('%B %Y')}):")
            
            # Check bill items
            items = bill.items.all()
            if not items.exists():
                self.stdout.write(self.style.ERROR("No bill items found"))
                has_errors = True
                continue
            
            # Calculate total from items
            calculated_total = Decimal(0)
            for item in items:
                calculated_total += item.amount
                
                # Verify item calculations
                if item.amount != item.quantity * item.service_price_at_billing:
                    self.stdout.write(self.style.ERROR(f"Item {item.id} calculation error:"))
                    self.stdout.write(self.style.ERROR(f"  Amount {item.amount} != quantity {item.quantity} * price {item.service_price_at_billing}"))
                    has_errors = True
            
            # Verify bill total
            if bill.total_amount != calculated_total:
                self.stdout.write(self.style.ERROR(f"Bill total mismatch:"))
                self.stdout.write(self.style.ERROR(f"  Bill total: {bill.total_amount}"))
                self.stdout.write(self.style.ERROR(f"  Calculated total: {calculated_total}"))
                has_errors = True
            
            # Check payment status
            if bill.is_paid and not bill.payment_date:
                self.stdout.write(self.style.ERROR("Bill marked as paid but has no payment date"))
                has_errors = True
            
            # Check duplicate bills
            duplicates = Bill.objects.filter(
                student=bill.student,
                month=bill.month
            ).exclude(id=bill.id)
            
            if duplicates.exists():
                self.stdout.write(self.style.ERROR("Duplicate bill detected:"))
                for dup in duplicates:
                    self.stdout.write(f"  Duplicate bill: {dup.id}")
                has_errors = True
            
            if not has_errors:
                self.stdout.write(self.style.SUCCESS("Bill is valid"))
        
        # Check for students without bills
        students_without_bills = Student.objects.filter(
            bills__isnull=True
        )
        
        if students_without_bills.exists():
            self.stdout.write(self.style.WARNING("\nStudents without bills:"))
            for student in students_without_bills:
                self.stdout.write(f"  {student}")
        
        if has_errors:
            self.stdout.write(self.style.ERROR("\nERROR: Some bills have issues!"))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\nAll bills are valid!"))
