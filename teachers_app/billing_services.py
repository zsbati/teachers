from django.db import models
from decimal import Decimal

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
