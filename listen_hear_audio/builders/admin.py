from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Property, PhaseInstallation, PurchasedPackage, PropertyNote, phase_order_annotation
from .tasks import send_property_creation_email, send_date_confirmation_email


class PhaseInstallationInline(admin.StackedInline):
    """Inline for phase installations showing packages in each phase"""
    model = PhaseInstallation
    extra = 0
    can_delete = False

    fields = (
        'status',
        'phase',
        'packages_display',
        ('requested_date', 'alternate_dates_display'),
        'builder_notes',
        ('confirmed_date', 'estimated_end_date'),
        'company_notes',
    )

    readonly_fields = (
        'phase', 'packages_display', 'alternate_dates_display',
        'requested_date', 'builder_notes',
    )

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['confirmed_date'].help_text = (
            'Note: Change status to Scheduled, select a date, add optional end date, then save at bottom to confirm.'
        )
        return formset

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _phase_order=phase_order_annotation()
        ).order_by('_phase_order')

    def packages_display(self, obj):
        """Show category and package name for each package"""
        if not obj.pk:
            return "-"
        packages = obj.get_packages()
        if not packages.exists():
            return "No packages"
        items = []
        for p in packages:
            qty = f" (x{p.quantity})" if p.quantity > 1 else ""
            items.append(f"<div style='margin-bottom:4px;'><strong>{p.category_snapshot}</strong><br><span style='color:#666;margin-left:12px;'>{p.package_name}{qty}</span></div>")
        return format_html("".join(items))
    packages_display.short_description = 'Category / Package'

    def alternate_dates_display(self, obj):
        if obj.pk:
            return obj.get_alternate_dates_display()
        return "-"
    alternate_dates_display.short_description = 'Alternates'


class PurchasedPackageInline(admin.TabularInline):
    """Simple inline showing all packages"""
    model = PurchasedPackage
    extra = 0
    can_delete = False
    fields = ('category_snapshot', 'package_name', 'installation_phase_snapshot', 'quantity')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class PropertyNoteInline(admin.TabularInline):
    """Inline for property notes"""
    model = PropertyNote
    extra = 0
    fields = ('note_type', 'message', 'created_by', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin for Property"""
    list_display = ('name', 'address_short', 'property_type', 'get_builders', 'phase_summary', 'updated_at')
    list_filter = ('property_type', 'created_at')
    search_fields = ('name', 'address')
    filter_horizontal = ('builders',)
    inlines = [PhaseInstallationInline, PurchasedPackageInline, PropertyNoteInline]
    readonly_fields = ('created_at', 'updated_at', 'quote_link')

    fieldsets = (
        (None, {
            'fields': ('name', 'address', 'property_type')
        }),
        ('Builders & Quote', {
            'fields': ('builders', 'quote_request', 'quote_link'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_builders(self, obj):
        builders = obj.builders.all()
        if builders:
            return ", ".join([b.company_name or b.email for b in builders])
        return "-"
    get_builders.short_description = 'Builders'

    def address_short(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Address'

    def phase_summary(self, obj):
        """Show phase status summary"""
        summary = obj.get_phase_summary()
        badges = []

        if summary['requested'] > 0:
            badges.append(format_html(
                '<span style="background:#ffc107;color:#212529;padding:2px 6px;border-radius:3px;font-size:11px;margin-right:4px;">{} Requested</span>',
                summary['requested']
            ))
        if summary['scheduled'] > 0:
            badges.append(format_html(
                '<span style="background:#0d6efd;color:white;padding:2px 6px;border-radius:3px;font-size:11px;margin-right:4px;">{} Scheduled</span>',
                summary['scheduled']
            ))
        if summary['completed'] > 0:
            badges.append(format_html(
                '<span style="background:#198754;color:white;padding:2px 6px;border-radius:3px;font-size:11px;">{} Done</span>',
                summary['completed']
            ))

        if not badges:
            return format_html('<span style="color:#6c757d;">{} phases</span>', summary['total'])

        return format_html(''.join([str(b) for b in badges]))
    phase_summary.short_description = 'Phases'

    def quote_link(self, obj):
        if obj.quote_request:
            url = reverse('admin:quotes_quoterequest_change', args=[obj.quote_request.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.quote_request.quote_number)
        return "-"
    quote_link.short_description = 'Quote'

    def save_model(self, request, obj, form, change):
        is_new = not change
        super().save_model(request, obj, form, change)

        if is_new and obj.builders.exists():
            send_property_creation_email.delay(obj.id)

    def save_formset(self, request, form, formset, change):
        """Detect status/date changes on PhaseInstallation inlines and log notes."""
        if formset.model is not PhaseInstallation:
            super().save_formset(request, form, formset, change)
            return

        email_phase_ids = []
        instances = formset.save(commit=False)

        for instance in instances:
            if instance.pk:
                try:
                    original = PhaseInstallation.objects.get(pk=instance.pk)
                except PhaseInstallation.DoesNotExist:
                    instance.save()
                    continue

                date_changed = original.confirmed_date != instance.confirmed_date and instance.confirmed_date
                status_explicitly_changed = original.status != instance.status

                if date_changed and instance.status == 'requested':
                    instance.status = 'scheduled'
                    status_explicitly_changed = False

                if date_changed:
                    PropertyNote.objects.create(
                        property=instance.property,
                        phase_installation=instance,
                        note_type='date_confirmation',
                        message=f"{instance.get_phase_display()} install date updated: {instance.get_confirmed_dates_display()}",
                        created_by=request.user,
                    )
                    email_phase_ids.append(instance.pk)

                if status_explicitly_changed:
                    PropertyNote.objects.create(
                        property=instance.property,
                        phase_installation=instance,
                        note_type='status_change',
                        message=f"{instance.get_phase_display()} status changed: {original.get_status_display()} → {instance.get_status_display()}",
                        created_by=request.user,
                    )

            instance.save()

        formset.save_m2m()

        for phase_id in email_phase_ids:
            send_date_confirmation_email.delay(phase_id)


@admin.register(PhaseInstallation)
class PhaseInstallationAdmin(admin.ModelAdmin):
    """Admin for Phase Installations"""
    list_display = (
        'property_link', 'phase_badge', 'status_badge', 'package_count',
        'requested_date', 'confirmed_dates_display'
    )
    list_filter = ('status', 'phase', 'requested_date', 'confirmed_date')
    search_fields = ('property__name', 'property__address')
    readonly_fields = (
        'packages_display', 'requested_date', 'alternate_dates_display',
        'builder_notes',
    )
    actions = ['confirm_dates', 'mark_in_progress', 'mark_completed', 'revert_to_scheduled', 'revert_to_in_progress']

    fieldsets = (
        (None, {
            'fields': ('status', 'property', 'phase')
        }),
        ('Category / Package', {
            'fields': ('packages_display',),
        }),
        ('Requested by Builder', {
            'fields': ('requested_date', 'alternate_dates_display', 'builder_notes'),
            'description': 'These fields are set by the builder and cannot be edited here.',
        }),
        ('Confirm Installation', {
            'fields': ('confirmed_date', 'estimated_end_date', 'company_notes', 'completion_date'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _phase_order=phase_order_annotation()
        ).order_by('_phase_order')

    def property_link(self, obj):
        url = reverse('admin:builders_property_change', args=[obj.property.pk])
        return format_html('<a href="{}">{}</a>', url, obj.property.name)
    property_link.short_description = 'Property'

    def phase_badge(self, obj):
        colors = {
            'framing': '#28a745',
            'rough_ins': '#17a2b8',
            'insulation_drywall': '#ffc107',
            'trim_finishes': '#fd7e14',
            'finished_property': '#0d6efd',
        }
        color = colors.get(obj.phase, '#6c757d')
        text_color = '#212529' if obj.phase == 'insulation_drywall' else 'white'
        return format_html(
            '<span style="background:{};color:{};padding:3px 8px;border-radius:3px;font-size:11px;font-weight:500;">{}</span>',
            color, text_color, obj.get_phase_display()
        )
    phase_badge.short_description = 'Phase'

    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'requested': '#ffc107',
            'scheduled': '#0d6efd',
            'in_progress': '#6f42c1',
            'completed': '#198754',
        }
        color = colors.get(obj.status, '#6c757d')
        text_color = '#212529' if obj.status == 'requested' else 'white'
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:3px;font-size:11px;font-weight:500;">{}</span>',
            color, text_color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def packages_display(self, obj):
        """Show category and package name for each package"""
        packages = obj.get_packages()
        if not packages.exists():
            return "No packages"
        items = []
        for p in packages:
            qty = f" (x{p.quantity})" if p.quantity > 1 else ""
            items.append(f"<div style='margin-bottom:4px;'><strong>{p.category_snapshot}</strong><br><span style='color:#666;margin-left:12px;'>{p.package_name}{qty}</span></div>")
        return format_html("".join(items))
    packages_display.short_description = 'Category / Package'

    def alternate_dates_display(self, obj):
        return obj.get_alternate_dates_display()
    alternate_dates_display.short_description = 'Alternates'

    def confirmed_dates_display(self, obj):
        return obj.get_confirmed_dates_display()
    confirmed_dates_display.short_description = 'Confirmed'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['confirmed_date'].help_text = (
            'Note: Change status to Scheduled, select a date, add optional end date, then save at bottom to confirm.'
        )
        return form

    def confirm_dates(self, request, queryset):
        """Confirm requested dates"""
        updated = 0
        for phase in queryset.filter(status='requested', requested_date__isnull=False):
            phase.confirmed_date = phase.requested_date
            phase.status = 'scheduled'
            phase.save()

            PropertyNote.objects.create(
                property=phase.property,
                phase_installation=phase,
                note_type='date_confirmation',
                message=f"{phase.get_phase_display()} confirmed: {phase.confirmed_date}",
                created_by=request.user
            )

            send_date_confirmation_email.delay(phase.id)
            updated += 1

        self.message_user(request, f'{updated} phase(s) confirmed.')
    confirm_dates.short_description = 'Confirm requested dates'

    def mark_in_progress(self, request, queryset):
        updated = 0
        for phase in queryset.filter(status='scheduled'):
            phase.status = 'in_progress'
            phase.save()
            updated += 1
        self.message_user(request, f'{updated} phase(s) marked in progress.')
    mark_in_progress.short_description = 'Mark In Progress'

    def mark_completed(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for phase in queryset.filter(status='in_progress'):
            phase.status = 'completed'
            if not phase.completion_date:
                phase.completion_date = timezone.now().date()
            phase.save()
            updated += 1
        self.message_user(request, f'{updated} phase(s) completed.')
    mark_completed.short_description = 'Mark Completed'

    def revert_to_scheduled(self, request, queryset):
        """Emergency revert: in_progress or completed → scheduled"""
        updated = 0
        for phase in queryset.filter(status__in=['in_progress', 'completed']):
            old_display = phase.get_status_display()
            phase.status = 'scheduled'
            phase.save()
            PropertyNote.objects.create(
                property=phase.property,
                phase_installation=phase,
                note_type='status_change',
                message=f"{phase.get_phase_display()} reverted from {old_display} to Scheduled",
                created_by=request.user,
            )
            updated += 1
        self.message_user(request, f'{updated} phase(s) reverted to Scheduled.')
    revert_to_scheduled.short_description = 'Revert to Scheduled (emergency)'

    def revert_to_in_progress(self, request, queryset):
        """Emergency revert: completed → in_progress"""
        updated = 0
        for phase in queryset.filter(status='completed'):
            phase.status = 'in_progress'
            phase.save()
            PropertyNote.objects.create(
                property=phase.property,
                phase_installation=phase,
                note_type='status_change',
                message=f"{phase.get_phase_display()} reverted from Completed to In Progress",
                created_by=request.user,
            )
            updated += 1
        self.message_user(request, f'{updated} phase(s) reverted to In Progress.')
    revert_to_in_progress.short_description = 'Revert to In Progress (emergency)'

    def save_model(self, request, obj, form, change):
        if change:
            original = PhaseInstallation.objects.get(pk=obj.pk)

            date_changed = original.confirmed_date != obj.confirmed_date and obj.confirmed_date
            status_explicitly_changed = original.status != obj.status

            # Auto-promote to scheduled when date is set on a requested phase
            if date_changed and obj.status == 'requested':
                obj.status = 'scheduled'
                status_explicitly_changed = False  # auto-promotion, not explicit

            if date_changed:
                PropertyNote.objects.create(
                    property=obj.property,
                    phase_installation=obj,
                    note_type='date_confirmation',
                    message=f"{obj.get_phase_display()} install date updated: {obj.get_confirmed_dates_display()}",
                    created_by=request.user,
                )
                send_date_confirmation_email.delay(obj.id)

            if status_explicitly_changed:
                PropertyNote.objects.create(
                    property=obj.property,
                    phase_installation=obj,
                    note_type='status_change',
                    message=f"{obj.get_phase_display()} status changed: {original.get_status_display()} → {obj.get_status_display()}",
                    created_by=request.user,
                )

        super().save_model(request, obj, form, change)


@admin.register(PurchasedPackage)
class PurchasedPackageAdmin(admin.ModelAdmin):
    """Admin for Purchased Packages"""
    list_display = ('category_snapshot', 'package_name', 'property_link', 'phase_badge', 'quantity')
    list_filter = ('installation_phase_snapshot', 'category_snapshot')
    search_fields = ('package_name', 'category_snapshot', 'property__name')

    def property_link(self, obj):
        url = reverse('admin:builders_property_change', args=[obj.property.pk])
        return format_html('<a href="{}">{}</a>', url, obj.property.name)
    property_link.short_description = 'Property'

    def phase_badge(self, obj):
        colors = {
            'framing': '#28a745',
            'rough_ins': '#17a2b8',
            'insulation_drywall': '#ffc107',
            'trim_finishes': '#fd7e14',
            'finished_property': '#0d6efd',
        }
        color = colors.get(obj.installation_phase_snapshot, '#6c757d')
        text_color = '#212529' if obj.installation_phase_snapshot == 'insulation_drywall' else 'white'
        phase_labels = {
            'framing': 'Framing',
            'rough_ins': 'Rough-Ins',
            'insulation_drywall': 'Insulation/Drywall',
            'trim_finishes': 'Trim/Finishes',
            'finished_property': 'Finished Property',
        }
        label = phase_labels.get(obj.installation_phase_snapshot, obj.installation_phase_snapshot or 'N/A')
        return format_html(
            '<span style="background:{};color:{};padding:3px 8px;border-radius:3px;font-size:11px;font-weight:500;">{}</span>',
            color, text_color, label
        )
    phase_badge.short_description = 'Phase'

    def has_add_permission(self, request):
        return False


@admin.register(PropertyNote)
class PropertyNoteAdmin(admin.ModelAdmin):
    """Admin for Property Notes"""
    list_display = ('property', 'note_type', 'message_preview', 'created_by', 'created_at')
    list_filter = ('note_type', 'created_at')
    search_fields = ('property__name', 'message')
    readonly_fields = ('created_at',)

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
