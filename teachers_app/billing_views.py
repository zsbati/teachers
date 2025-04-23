from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from .models import Student, Task, WorkSession, Service
from .billing_models import Bill, BillItem
from .forms import BillItemForm

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_bill(request, student_id):
    """Create or update a bill for a student"""
    student = get_object_or_404(Student, pk=student_id)
    current_month = timezone.now().replace(day=1)
    
    # Get existing bill for this month if it exists
    bill = Bill.objects.filter(student=student, month=current_month).first()
    
    if request.method == 'POST':
        form = BillItemForm(request.POST)
        if form.is_valid():
            if not bill:
                bill = Bill.objects.create(
                    student=student,
                    month=current_month,
                    total_amount=0  # Will be calculated later
                )
            
            # Create bill item
            bill_item = form.save(commit=False)
            bill_item.bill = bill
            
            # Get the service from the form
            service = form.cleaned_data['service']
            quantity = form.cleaned_data['quantity']
            
            # Set all required fields
            bill_item.service_name = service.name
            bill_item.service_description = service.description if service.description else ''
            bill_item.service_price_at_billing = service.price
            bill_item.quantity = quantity
            bill_item.amount = service.price * quantity
            
            bill_item.save()
            
            # Recalculate total amount
            bill.total_amount = bill.items.aggregate(
                total=Sum('amount')
            )['total']
            bill.save()
            
            messages.success(request, f'Service added to bill. Total amount: ${bill.total_amount}')
            return redirect('create_bill', student_id=student_id)
    else:
        form = BillItemForm()
    
    # Get work sessions for this month
    work_sessions = WorkSession.objects.filter(
        start_time__date__gte=current_month,
        start_time__date__lt=current_month + relativedelta(months=1)
    ).order_by('start_time')
    
    # Calculate total hours
    total_hours = work_sessions.aggregate(
        total_hours=Sum('stored_hours')
    )['total_hours']
    
    # Get active services
    services = Service.objects.filter(is_active=True)
    
    # Get existing bill items if bill exists
    bill_items = bill.items.all() if bill else []
    
    context = {
        'student': student,
        'bill': bill,
        'work_sessions': work_sessions,
        'total_hours': total_hours,
        'services': services,
        'bill_items': bill_items,
        'current_month': current_month,
        'form': form
    }
    
    return render(request, 'superuser/create_bill.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def select_student_for_bill_creation(request):
    """View to select a student for bill creation"""
    students = Student.objects.all()
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if student_id:
            return redirect('create_bill', student_id=student_id)
    
    return render(request, 'superuser/select_student_for_bill.html', {
        'students': students
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def select_student_for_billing(request):
    """View to select a student for billing"""
    students = Student.objects.all()
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if student_id:
            return redirect('student_bills', student_id=student_id)
    
    return render(request, 'superuser/select_student_billing.html', {
        'students': students
    })

@login_required
def student_bills(request, student_id):
    """View student's bills"""
    student = get_object_or_404(Student, pk=student_id)
    bills = Bill.objects.filter(student=student).order_by('-month')
    
    return render(request, 'student/bills.html', {
        'student': student,
        'bills': bills
    })

@login_required
def bill_detail(request, bill_id):
    """View bill details"""
    bill = get_object_or_404(Bill, pk=bill_id)
    
    return render(request, 'student/bill_detail.html', {
        'bill': bill,
        'total': bill.items.aggregate(Sum('amount'))['amount__sum']
    })
