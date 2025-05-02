from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Teacher, SalaryReport
from .services import SalaryCalculationService
from .forms import SalaryReportForm
import calendar

@login_required
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def salary_reports_bulk(request):
    """
    Bulk salary report creation/updating for all teachers for a selected month, with preview and update/skip logic.
    """
    today = timezone.now().date()
    default_month = (today.replace(day=1) - relativedelta(months=1))
    month = int(request.GET.get('month', default_month.month))
    year = int(request.GET.get('year', default_month.year))
    month_start = timezone.make_aware(timezone.datetime(year, month, 1))
    if month == 12:
        month_end = timezone.make_aware(timezone.datetime(year + 1, 1, 1))
    else:
        month_end = timezone.make_aware(timezone.datetime(year, month + 1, 1))
    month_end = month_end - timezone.timedelta(microseconds=1)

    teachers = Teacher.objects.all()
    preview_data = []
    for teacher in teachers:
        report = SalaryReport.objects.filter(teacher=teacher, start_date=month_start, end_date=month_end, is_deleted=False).first()
        is_paid = getattr(report, 'is_paid', False) if report else False
        preview_data.append({
            'teacher': teacher,
            'report': report,
            'already_exists': bool(report),
            'paid': is_paid,
        })

    if request.method == 'POST':
        actions = []
        for item in preview_data:
            action = request.POST.get(f'action_{item["teacher"].id}', 'skip')
            if not item['already_exists'] and action == 'create':
                # Create salary report
                SalaryReport.create_for_month(
                    teacher=item['teacher'],
                    year=year,
                    month=month,
                    created_by=request.user,
                )
                actions.append({'teacher': item['teacher'], 'action': 'created'})
            elif item['already_exists']:
                if action == 'update' and item['report']:
                    # Update: Recalculate and update totals (simulate update)
                    report = item['report']
                    report_data = SalaryCalculationService.calculate_salary(item['teacher'], year, month)
                    report.total_hours = report_data.get('total_hours')
                    report.total_amount = report_data.get('total_salary')
                    report.save(update_fields=['total_hours', 'total_amount'])
                    actions.append({'teacher': item['teacher'], 'action': 'updated'})
                elif action == 'skip':
                    actions.append({'teacher': item['teacher'], 'action': 'skipped'})
        return render(request, 'superuser/salary_reports_bulk_result.html', {'actions': actions, 'month': month, 'year': year})

    # Prepare months list for template (1-based)
    months = [
        {'value': i, 'name': calendar.month_name[i]} for i in range(1, 13)
    ]

    return render(request, 'superuser/salary_reports_bulk_preview.html', {
        'preview_data': preview_data,
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'months': months,
    })

@login_required
@user_passes_test(lambda u: u.is_inspector, login_url=None)
def create_salary_report(request):
    if request.method == 'POST':
        form = SalaryReportForm(request.POST)
        if form.is_valid():
            teacher = form.cleaned_data['teacher']
            year = form.cleaned_data['year']
            month = int(form.cleaned_data['month'])
            notes = form.cleaned_data['notes']

            # Create start and end dates for the month
            start_date = timezone.datetime(year, month, 1)
            if month == 12:
                end_date = timezone.datetime(year + 1, 1, 1)
            else:
                end_date = timezone.datetime(year, month + 1, 1)
            end_date = end_date - timezone.timedelta(microseconds=1)

            # Create the report
            report = SalaryReport.objects.create(
                teacher=teacher,
                start_date=start_date,
                end_date=end_date,
                created_by=request.user,
                notes=notes
            )
            report_data = SalaryCalculationService.calculate_salary(teacher, year, month)
            
            # Since we're always creating a new report, we don't need to check if it was created
            message = f'Salary report created for {teacher.user.username} - {report_data["period"]}'
            messages.success(request, message)
            
            return redirect('view_salary_report', teacher_id=teacher.id, year=year, month=month)
    else:
        form = SalaryReportForm()

    return render(request, 'superuser/create_salary_report.html', {
        'form': form
    })
