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
        import logging
        logger = logging.getLogger(__name__)
        
        # Log the incoming work session data
        logger.debug(f"Processing work session: {work_session.task.name}, price: {work_session.task.price}, hours: {work_session.stored_hours}")
        
        # Only create bill item if we have a student AND stored_hours is not None
        if work_session.student and work_session.stored_hours is not None:
            # Get task price and stored hours
            service_price = work_session.task.price
            quantity = work_session.stored_hours
            
            # Calculate bill amount (0 for free tasks)
            amount = service_price * quantity if service_price > 0 else Decimal('0.00')
            logger.debug(f"Calculated bill amount: {amount} (type: {type(amount)})")
            
            # Skip bill item creation for free tasks
            if amount == 0 or amount == Decimal('0.00'):
                logger.debug("Free task - skipping bill item creation")
                return None
            
            # Determine the billing month (first day of the session's month)
            session_date = work_session.created_at.date() if work_session.created_at else date.today()
            
            # Rest of the bill item creation logic...
            
        # If no student or not clocked out yet, just return None
        logger.debug("No bill item created - either no student or hours not calculated yet")
        return None
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
            service_price_at_billing=service_price,
            quantity=quantity,
            amount=amount
        )
        
        # Update the Bill's total amount
        bill.total_amount = BillItem.objects.filter(
            bill=bill,
            service_price_at_billing__gt=0,
            amount__gt=0
        ).aggregate(
            total=models.Sum('amount', default=0)
        )['total']
        bill.save()
        
        return bill_item
        
