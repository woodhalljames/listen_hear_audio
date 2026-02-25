from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime

from .models import Property, PhaseInstallation, PurchasedPackage, PropertyNote
from .tasks import send_date_request_email
from listen_hear_audio.products.models import Package, Category


class BuilderRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is a builder"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_builder


class BuilderPropertyDetailView(BuilderRequiredMixin, DetailView):
    """Detailed view of a single property for builder"""
    model = Property
    template_name = 'builders/builder_property_detail.html'
    context_object_name = 'property'
    slug_field = 'quote_request__quote_number'
    slug_url_kwarg = 'quote_number'

    def get_queryset(self):
        """Only show properties assigned to this builder"""
        return Property.objects.filter(
            builders=self.request.user
        ).select_related('quote_request').prefetch_related('packages', 'phase_installations', 'notes', 'builders')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        property_obj = self.object
        packages = property_obj.packages.all()

        # Build phases data with packages grouped
        phases_data = []
        phase_order = ['framing', 'rough_ins', 'insulation_drywall', 'trim_finishes', 'finished_property']
        phase_labels = {
            'framing': 'Framing',
            'rough_ins': 'Rough-Ins',
            'insulation_drywall': 'Insulation & Drywall',
            'trim_finishes': 'Trim & Finishes',
            'finished_property': 'Finished Property',
        }

        for phase_key in phase_order:
            phase_packages = packages.filter(installation_phase_snapshot=phase_key)
            if phase_packages.exists():
                # Get or create phase installation record
                phase_install, created = PhaseInstallation.objects.get_or_create(
                    property=property_obj,
                    phase=phase_key,
                    defaults={'status': 'pending'}
                )

                phases_data.append({
                    'key': phase_key,
                    'label': phase_labels.get(phase_key, phase_key),
                    'packages': phase_packages,
                    'installation': phase_install,
                    'icon': _get_phase_icon(phase_key),
                })

        context['phases'] = phases_data

        # Build unified activity timeline
        timeline = []

        # Track which phases already have a confirmation entry (from PhaseInstallation)
        confirmed_phase_ids = set()

        # Date confirmations — built directly from phase installations with confirmed_date
        for phase_data in phases_data:
            inst = phase_data['installation']
            if inst.confirmed_date:
                confirmed_phase_ids.add(inst.pk)
                timeline.append({
                    'type': 'date_confirmation',
                    'message': f"{phase_data['label']} confirmed: {inst.get_confirmed_dates_display()}",
                    'date': inst.updated_at,
                    'phase_label': phase_data['label'],
                    'builder_notes': '',
                    'company_notes': inst.company_notes or '',
                })

        # PropertyNote entries — date_request (with builder notes), status_change, general
        for note in property_obj.notes.select_related('created_by', 'phase_installation').all()[:20]:
            # Skip date_confirmation PropertyNotes — already covered above
            if note.note_type == 'date_confirmation':
                continue

            entry = {
                'type': note.note_type,
                'message': note.message,
                'date': note.created_at,
                'phase_label': note.phase_installation.get_phase_display() if note.phase_installation else '',
                'builder_notes': '',
                'company_notes': '',
            }

            # Merge builder_notes for date requests
            if note.note_type == 'date_request' and note.phase_installation:
                entry['builder_notes'] = note.phase_installation.builder_notes or ''

            timeline.append(entry)

        timeline.sort(key=lambda x: x['date'], reverse=True)
        context['timeline'] = timeline

        # Get phase summary
        context['phase_summary'] = property_obj.get_phase_summary()

        return context


@login_required
@require_POST
def request_phase_install(request, property_id, phase):
    """Builder requests installation date for a phase"""

    if not request.user.is_builder:
        messages.error(request, 'Not authorized')
        return redirect('home')

    property_obj = get_object_or_404(Property.objects.select_related('quote_request'), pk=property_id)

    # Verify builder has access
    if not property_obj.builders.filter(pk=request.user.pk).exists():
        messages.error(request, 'Not authorized')
        return redirect('home')

    # Helper to redirect back to property detail
    def _redirect_to_property():
        return redirect(property_obj.get_absolute_url())

    # Get or create phase installation
    phase_install, created = PhaseInstallation.objects.get_or_create(
        property=property_obj,
        phase=phase,
        defaults={'status': 'pending'}
    )

    # Only allow requesting if pending
    if phase_install.status != 'pending':
        messages.warning(request, 'Date already requested for this phase')
        return _redirect_to_property()

    # Get form data
    preferred_dates = request.POST.getlist('preferred_dates')
    builder_notes = request.POST.get('builder_notes', '')

    if not preferred_dates or not any(preferred_dates):
        messages.error(request, 'Please provide at least one date')
        return _redirect_to_property()

    # Parse dates
    valid_dates = []
    for date_str in preferred_dates:
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                valid_dates.append(parsed_date)
            except ValueError:
                pass

    if not valid_dates:
        messages.error(request, 'Please provide a valid date')
        return _redirect_to_property()

    # Update phase installation
    primary_date = valid_dates[0]
    alternate_dates = [d.strftime('%Y-%m-%d') for d in valid_dates[1:]] if len(valid_dates) > 1 else []

    phase_install.requested_date = primary_date
    phase_install.alternate_dates = alternate_dates
    phase_install.builder_notes = builder_notes
    phase_install.status = 'requested'
    phase_install.save()

    # Create activity note
    dates_msg = primary_date.strftime('%m/%d/%Y')
    if alternate_dates:
        dates_msg += f" (alternates: {', '.join([datetime.strptime(d, '%Y-%m-%d').strftime('%m/%d/%Y') for d in alternate_dates])})"

    PropertyNote.objects.create(
        property=property_obj,
        phase_installation=phase_install,
        note_type='date_request',
        message=f"{phase_install.get_phase_display()} requested for {dates_msg}",
        created_by=request.user
    )

    # Send email to admin
    send_date_request_email.delay(phase_install.id)

    messages.success(request, f'Install date requested for {phase_install.get_phase_display()}')
    return _redirect_to_property()


def builder_showroom_intro(request):
    """Landing page for builder showroom"""
    return render(request, 'builders/builder_showroom_intro.html')


def _get_section_icon(section):
    """Get Bootstrap icon for builder section"""
    icons = {
        'pre_wire': 'bi-bezier2',
        'automations': 'bi-lightbulb',
        'entertainment_audio': 'bi-speaker',
        'custom_solutions': 'bi-puzzle',
    }
    return icons.get(section, 'bi-box')


def _get_phase_icon(phase):
    """Get Bootstrap icon for installation phase"""
    icons = {
        'framing': 'bi-grid-3x3-gap',
        'rough_ins': 'bi-router',
        'insulation_drywall': 'bi-layers',
        'trim_finishes': 'bi-paint-bucket',
        'finished_property': 'bi-house-check',
    }
    return icons.get(phase, 'bi-box')


def builder_showroom(request, step=1):
    """Guided step-by-step builder showroom experience."""
    from listen_hear_audio.quotes.cart import get_or_create_cart

    cart = get_or_create_cart(request)
    cart_package_ids = list(cart.items.values_list('package_id', flat=True))

    all_sections = []
    for section_value, section_label in Category.BUILDER_SECTION_CHOICES:
        categories = Category.objects.filter(
            builder_section=section_value,
            is_active=True
        ).prefetch_related('packages', 'subcategories__packages').order_by('display_order', 'name')

        packages = Package.objects.filter(
            category__builder_section=section_value,
            category__is_active=True,
            is_active=True,
            visibility__in=['both', 'showroom'],
        ).select_related('category', 'subcategory').order_by('display_order', 'name')

        if categories.exists() or packages.exists():
            all_sections.append({
                'key': section_value,
                'label': section_label,
                'categories': categories,
                'packages': packages,
                'icon': _get_section_icon(section_value)
            })

    total_steps = len(all_sections)

    if step < 1 or step > total_steps:
        messages.error(request, 'Invalid step')
        return redirect('builders:showroom_guided')

    context = {
        'current_step': step,
        'total_steps': total_steps,
        'all_sections': all_sections,
        'has_previous': step > 1,
        'has_next': step < total_steps,
        'cart_count': cart.get_total_items(),
        'cart_package_ids': cart_package_ids,
    }

    return render(request, 'builders/builder_showroom_guided.html', context)
