from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime

from .models import Property, PurchasedPackage, PropertyNote


class BuilderRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is a builder"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_builder


class BuilderDashboardView(BuilderRequiredMixin, ListView):
    """Builder dashboard showing all assigned properties"""
    model = Property
    template_name = 'builders/builder_dashboard.html'
    context_object_name = 'properties'

    def get_queryset(self):
        """Get properties assigned to this builder"""
        return Property.objects.filter(
            builders=self.request.user
        ).prefetch_related('packages', 'builders').order_by('-updated_at')


class BuilderPropertyDetailView(BuilderRequiredMixin, DetailView):
    """Detailed view of a single property for builder"""
    model = Property
    template_name = 'builders/builder_property_detail.html'
    context_object_name = 'property'

    def get_queryset(self):
        """Only show properties assigned to this builder"""
        return Property.objects.filter(
            builders=self.request.user
        ).prefetch_related('packages', 'notes', 'builders')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get packages grouped by status
        property_obj = self.object
        packages = property_obj.packages.all()

        context['packages_pending'] = packages.filter(status='pending')
        context['packages_date_requested'] = packages.filter(status='date_requested')
        context['packages_scheduled'] = packages.filter(status='scheduled')
        context['packages_in_progress'] = packages.filter(status='in_progress')
        context['packages_completed'] = packages.filter(status='completed').order_by('-completion_date')

        # Get activity timeline
        context['notes'] = property_obj.notes.select_related('created_by', 'package').all()[:20]

        # Get status summary
        context['status_summary'] = property_obj.get_package_status_summary()

        return context


@login_required
@require_POST
def request_install_date(request, package_id):
    """Builder requests installation date for a package"""

    # Ensure user is a builder
    if not request.user.is_builder:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    package = get_object_or_404(PurchasedPackage, pk=package_id)

    # Verify builder has access to this property
    if not package.property.builders.filter(pk=request.user.pk).exists():
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    # Get form data
    requested_date = request.POST.get('requested_date')
    builder_notes = request.POST.get('builder_notes', '')

    if not requested_date:
        return JsonResponse({'success': False, 'error': 'Date is required'}, status=400)

    # Parse date
    try:
        install_date = datetime.strptime(requested_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)

    # Update package
    package.requested_install_date = install_date
    package.builder_notes = builder_notes
    package.status = 'date_requested'
    package.save()

    # Create activity note
    PropertyNote.objects.create(
        property=package.property,
        package=package,
        note_type='date_request',
        message=f"Installation date requested for {install_date}. Notes: {builder_notes}" if builder_notes else f"Installation date requested for {install_date}",
        created_by=request.user
    )

    # Send email notification to company (you can implement this in tasks.py)
    # from listen_hear_audio.builders.tasks import notify_company_date_request
    # notify_company_date_request.delay(package.id)

    messages.success(request, f'Installation date requested for {package.package_name}')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Date request submitted',
            'package_id': package.id,
            'status': package.get_status_display()
        })

    return redirect('builders:property_detail', pk=package.property.pk)


@login_required
@require_POST
def update_package_notes(request, package_id):
    """Update builder notes on a package"""

    if not request.user.is_builder:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    package = get_object_or_404(PurchasedPackage, pk=package_id)

    # Verify builder has access
    if not package.property.builders.filter(pk=request.user.pk).exists():
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    builder_notes = request.POST.get('builder_notes', '')
    package.builder_notes = builder_notes
    package.save()

    messages.success(request, 'Notes updated')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Notes updated'})

    return redirect('builders:property_detail', pk=package.property.pk)
