from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from ..models import Service
from ..service_forms import ServiceForm

@login_required
@user_passes_test(lambda u: u.is_superuser or hasattr(u, 'inspector'), login_url=None)
def manage_services(request):
    """View to list and manage services"""
    services = Service.objects.all()
    return render(request, 'superuser/manage_services.html', {'services': services})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_service(request):
    """View to add a new service"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service added successfully')
            return redirect('manage_services')
    else:
        form = ServiceForm()
    return render(request, 'superuser/service_form.html', {
        'form': form,
        'title': 'Add Service'
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_service(request, service_id):
    """View to edit an existing service"""
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully')
            return redirect('manage_services')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'superuser/service_form.html', {
        'form': form,
        'title': 'Edit Service'
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_service(request, service_id):
    """View to delete a service"""
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted successfully')
        return redirect('manage_services')
    return render(request, 'superuser/confirm_delete.html', {
        'object': service,
        'object_name': 'service'
    })
