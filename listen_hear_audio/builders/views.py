from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime

from .models import Property, PurchasedPackage, PropertyNote
from .tasks import send_date_request_email
from listen_hear_audio.products.models import Package, Category, PropertyType


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

        # Group packages by installation phase for display
        from listen_hear_audio.products.models import Package
        packages_by_phase = {}
        for phase_value, phase_label in Package.INSTALLATION_PHASE_CHOICES:
            packages_by_phase[phase_value] = {
                'label': phase_label,
                'packages': packages.filter(installation_phase_snapshot=phase_value)
            }
        context['packages_by_phase'] = packages_by_phase

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

    # Send email notification to company
    send_date_request_email.delay(package.id)

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


def builder_showroom(request):
    """
    Builder showroom experience for walking clients through smart home packages.
    Organizes categories and packages by builder sections (Network & Automation, Security, Audio, Entertainment).
    If categories don't have builder_section set, they appear in an "Other" section.
    """
    from listen_hear_audio.quotes.cart import get_or_create_cart

    # Get cart for cart count
    cart = get_or_create_cart(request)

    # Get categories grouped by builder section
    sections_data = {}

    for section_value, section_label in Category.BUILDER_SECTION_CHOICES:
        # Get categories in this section
        categories = Category.objects.filter(
            builder_section=section_value,
            is_active=True
        ).prefetch_related('packages', 'subcategories__packages')

        # Get all packages from categories in this section
        packages = Package.objects.filter(
            category__builder_section=section_value,
            category__is_active=True,
            is_active=True
        ).select_related('category', 'subcategory').order_by('display_order', 'name')

        # Get categories with videos for this section
        categories_with_videos = categories.exclude(youtube_url='')

        sections_data[section_value] = {
            'label': section_label,
            'categories': categories,
            'packages': packages,
            'categories_with_videos': categories_with_videos,
            'icon': _get_section_icon(section_value)
        }

    # Add an "Other" section for categories without a builder_section
    categories_no_section = Category.objects.filter(
        builder_section='',
        is_active=True
    ).prefetch_related('packages', 'subcategories__packages')

    packages_no_section = Package.objects.filter(
        category__builder_section='',
        category__is_active=True,
        is_active=True
    ).select_related('category', 'subcategory').order_by('display_order', 'name')

    if categories_no_section.exists() or packages_no_section.exists():
        categories_with_videos_no_section = categories_no_section.exclude(youtube_url='')

        sections_data['other'] = {
            'label': 'Other Products',
            'categories': categories_no_section,
            'packages': packages_no_section,
            'categories_with_videos': categories_with_videos_no_section,
            'icon': 'bi-box-seam'
        }

    context = {
        'sections_data': sections_data,
        'cart_count': cart.get_total_items(),
    }

    return render(request, 'builders/builder_showroom.html', context)


def _get_section_icon(section):
    """Get Bootstrap icon for builder section"""
    icons = {
        'network_automation': 'bi-router',
        'security': 'bi-shield-check',
        'audio': 'bi-speaker',
        'entertainment': 'bi-play-circle',
    }
    return icons.get(section, 'bi-box')


def _get_phase_icon(phase):
    """Get Bootstrap icon for installation phase"""
    icons = {
        'framing': 'bi-grid-3x3-gap',
        'rough_ins': 'bi-router',
        'insulation_drywall': 'bi-layers',
        'trim_finishes': 'bi-paint-bucket',
    }
    return icons.get(phase, 'bi-box')
