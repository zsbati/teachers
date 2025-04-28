from django.db import models
from decimal import Decimal
from django.utils import timezone
from .models import Student

# Bill Model
class Bill(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bills')
    month = models.DateField(help_text="Billing month (first day of month)")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'month')
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.student} - {self.month.strftime('%B %Y')} - ${self.total_amount}"

# BillItem Model - Historical record of bill items
class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    service_name = models.CharField(max_length=200)
    service_description = models.TextField(blank=True)
    service_price_at_billing = models.DecimalField(max_digits=20, decimal_places=4)
    quantity = models.DecimalField(max_digits=20, decimal_places=4)
    amount = models.DecimalField(max_digits=20, decimal_places=4)
    
    def __str__(self):
        return f"{self.service_name} - ${self.amount}"
