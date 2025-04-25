from django.db import models
from decimal import Decimal
from datetime import date
from django.db import transaction
from .billing_models import Bill, BillItem

class StudentBillingService:
    @staticmethod
    def calculate_student_balance(student):
        """Calculate the current balance for a student"""
        # This will be implemented when we have the billing models
        return Decimal('0.00')

    @staticmethod
    def get_student_bills(student):
        """Get all bills for a student"""
        # This will be implemented when we have the billing models
        return []

    @staticmethod
    def create_bill_item_for_work_session(work_session):
        """
        Create a BillItem for a WorkSession if a student is associated. Finds or creates the Bill for the student for the current month.
        Updates the Bill's total_amount.
        """
        # Only proceed if the work session has a student
        if not work_session.student:
            return None
        
        # Determine the billing month (first day of the session's month)
        session_date = work_session.created_at.date() if work_session.created_at else date.today()
        billing_month = session_date.replace(day=1)
        
        # Find or create the Bill for this student and month
        bill, created = Bill.objects.get_or_create(
            student=work_session.student,
            month=billing_month,
            defaults={
                'total_amount': 0,
            }
        )
        
        # Create the BillItem
        bill_item = BillItem.objects.create(
            bill=bill,
            service_name=work_session.task.name,
            service_description=work_session.task.description or '',
            service_price_at_billing=work_session.task.price,
            quantity=work_session.stored_hours or 0,
            amount=work_session.total_amount or 0,
        )
        
        # Update the Bill's total_amount
        bill.total_amount = sum(item.amount for item in bill.items.all())
        bill.save(update_fields=['total_amount'])
        
        return bill_item
