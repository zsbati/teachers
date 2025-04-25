from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from .models import Student, Task, WorkSession, Service
from .billing_models import Bill, BillItem
from .forms import BillItemForm
import calendar

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
@user_passes_test(lambda u: u.is_inspector, login_url=None)
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
    
    return render(request, 'student/student_bills.html', {
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

@login_required
@user_passes_test(lambda u: u.is_superuser)
def bill_all_students(request):
    """Bulk billing for all students for a selected month, with preview and update/skip logic."""
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    from .models import Student, WorkSession, Service
    from .billing_models import Bill, BillItem
    from django.db.models import Sum
    import calendar

    # Get month/year from GET or POST, default to previous month
    today = timezone.now().date()
    default_month = (today.replace(day=1) - relativedelta(months=1))
    year = int(request.GET.get('year', default_month.year))
    month = int(request.GET.get('month', default_month.month))
    month_start = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
    month_end = (month_start + relativedelta(months=1))

    students = Student.objects.filter(is_active=True)
    bills = Bill.objects.filter(month=month_start)
    bills_by_student = {b.student_id: b for b in bills}

    preview_data = []
    for student in students:
        bill = bills_by_student.get(student.id)
        ws_count = WorkSession.objects.filter(student=student, start_time__gte=month_start, start_time__lt=month_end).count()
        preview_data.append({
            'student': student,
            'bill': bill,
            'already_billed': bool(bill),
            'paid': bill.is_paid if bill else False,
            'work_sessions': ws_count,
        })

    if request.method == 'POST' and 'confirm' in request.POST:
        # Superuser has confirmed choices
        actions = []
        for item in preview_data:
            sid = str(item['student'].id)
            if not item['already_billed']:
                # Create bill immediately, no confirmation needed
                bill = Bill.objects.create(student=item['student'], month=month_start, total_amount=0)
                # Here, add bill items as needed (simplified, real logic may differ)
                actions.append({'student': item['student'], 'action': 'created'})
            else:
                action = request.POST.get(f'action_{sid}')
                if action == 'update':
                    bill = item['bill']
                    # ... recalculate bill items here ...
                    actions.append({'student': item['student'], 'action': 'updated'})
                elif action == 'skip':
                    actions.append({'student': item['student'], 'action': 'skipped'})
        return render(request, 'superuser/bill_all_students_result.html', {'actions': actions, 'month': month, 'year': year})

    # Prepare months list for template (1-based)
    months = [
        {'value': i, 'name': calendar.month_name[i]} for i in range(1, 13)
    ]

    return render(request, 'superuser/bill_all_students_preview.html', {
        'preview_data': preview_data,
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'months': months,
    })
