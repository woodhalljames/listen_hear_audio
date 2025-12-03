from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import Cart, CartItem, QuoteRequest, QuoteRequestItem, SiteConfiguration


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['package', 'quantity', 'notes', 'added_at']
    can_delete = False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_display', 'session_key', 'total_items', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'session_key']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']
    
    def user_display(self, obj):
        return obj.user.email if obj.user else 'Guest'
    user_display.short_description = 'User'
    
    def total_items(self, obj):
        return obj.get_total_items()
    total_items.short_description = 'Items'


class QuoteRequestItemInline(admin.TabularInline):
    model = QuoteRequestItem
    extra = 1
    readonly_fields = ['price_display', 'subtotal_display']
    fields = ['package', 'package_name', 'package_description', 'quantity', 'price_snapshot', 'price_display', 'subtotal_display', 'notes']
    autocomplete_fields = ['package']

    def price_display(self, obj):
        if not obj.pk:  # New item
            return '-'
        if obj.price_snapshot is None:
            return format_html('<span style="color: #999;">Custom</span>')
        return f"${obj.price_snapshot:,.2f}"
    price_display.short_description = 'Unit Price'

    def subtotal_display(self, obj):
        if not obj.pk:  # New item
            return '-'
        if obj.price_snapshot is None:
            return format_html('<span style="color: #999;">Custom</span>')
        return f"${obj.get_subtotal():,.2f}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = [
        'quote_number',
        'contact_person',
        'email',
        'status',
        'finalized_status',
        'estimated_total_display',
        'final_total_display',
        'total_items_display',
        'property_status',
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'finalized_at']
    search_fields = ['quote_number', 'contact_person', 'email', 'phone']
    readonly_fields = [
        'quote_number',
        'user',
        'estimated_total',
        'created_at',
        'updated_at',
        'finalized_at',
        'finalized_by',
        'pdf_link',
        'property_link'
    ]
    inlines = [QuoteRequestItemInline]
    actions = ['finalize_quotes', 'regenerate_pdfs', 'convert_to_property']

    fieldsets = (
        ('Quote Information', {
            'fields': ('quote_number', 'status', 'user', 'estimated_total', 'pdf_link', 'property_link')
        }),
        ('Customer Contact', {
            'fields': ('contact_person', 'email', 'phone', 'website')
        }),
        ('Location', {
            'fields': ('street', 'city', 'state', 'zip_code')
        }),
        ('Customer Notes', {
            'fields': ('notes',),
            'description': 'Notes from the customer about their project requirements'
        }),
        ('Admin Finalization', {
            'fields': ('admin_notes', 'final_total', 'finalized_at', 'finalized_by'),
            'description': 'Use the "Finalize selected quotes" action to set finalized_at automatically',
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def estimated_total_display(self, obj):
        if obj.estimated_total is None:
            return format_html('<span style="color: #999;">Not calculated</span>')
        return f"${obj.estimated_total:,.2f}"
    estimated_total_display.short_description = 'Estimated'
    estimated_total_display.admin_order_field = 'estimated_total'

    def final_total_display(self, obj):
        if obj.final_total is None:
            return format_html('<span style="color: #999;">-</span>')
        return format_html('<strong style="color: #0a0;">${:,.2f}</strong>', obj.final_total)
    final_total_display.short_description = 'Final Quote'
    final_total_display.admin_order_field = 'final_total'

    def finalized_status(self, obj):
        if obj.is_finalized():
            return format_html('<span style="color: green;">✓ Finalized</span>')
        return format_html('<span style="color: #999;">Not finalized</span>')
    finalized_status.short_description = 'Finalized'

    def total_items_display(self, obj):
        return obj.get_total_items()
    total_items_display.short_description = 'Items'

    def pdf_link(self, obj):
        if not obj.pk:
            return "Save quote first"

        buttons = []

        # View existing PDF button
        if obj.pdf_path:
            buttons.append(
                f'<a href="{obj.pdf_path.url}" target="_blank" class="button" style="margin-right: 5px;">'
                '<i class="bi bi-file-pdf"></i> View PDF</a>'
            )

        # Generate/Download PDF button
        generate_url = reverse('admin:quotes_quoterequest_generate_pdf', args=[obj.pk])
        buttons.append(
            f'<a href="{generate_url}" class="button" style="margin-right: 5px;">'
            '<i class="bi bi-download"></i> Generate & Download</a>'
        )

        return format_html(' '.join(buttons))
    pdf_link.short_description = 'PDF Actions'

    def property_link(self, obj):
        """Show link to property if quote has been converted"""
        properties = obj.properties.all()
        if properties.exists():
            links = []
            for prop in properties:
                url = reverse('admin:builders_property_change', args=[prop.pk])
                links.append(format_html('<a href="{}" target="_blank">{}</a>', url, prop.name))
            return format_html('<br>'.join(links))
        return format_html('<span style="color: #999;">Not converted yet</span>')
    property_link.short_description = 'Property'

    def property_status(self, obj):
        """Show if quote has been converted to property"""
        if obj.properties.exists():
            return format_html('<span style="color: green;">✓ Converted</span>')
        return format_html('<span style="color: #999;">-</span>')
    property_status.short_description = 'Property'

    def finalize_quotes(self, request, queryset):
        """Finalize selected quotes and regenerate PDFs"""
        from django.utils import timezone
        from celery import chain
        from listen_hear_audio.quotes.tasks import generate_quote_pdf, send_quote_emails

        finalized_count = 0
        for quote in queryset:
            if not quote.is_finalized():
                quote.finalized_at = timezone.now()
                quote.finalized_by = request.user
                quote.status = 'quoted'

                # Recalculate estimated total if no final total is set
                if quote.final_total is None:
                    quote.recalculate_estimated_total()

                quote.save()

                # Regenerate PDF and send email
                task_chain = chain(
                    generate_quote_pdf.si(quote.id),
                    send_quote_emails.si(quote.id)
                )
                task_chain.apply_async()

                finalized_count += 1

        self.message_user(
            request,
            f'{finalized_count} quote(s) finalized. PDFs are being regenerated and emails will be sent.',
            level=messages.SUCCESS
        )
    finalize_quotes.short_description = 'Finalize selected quotes and send to customers'

    def regenerate_pdfs(self, request, queryset):
        """Regenerate PDFs for selected quotes without sending emails"""
        from listen_hear_audio.quotes.tasks import generate_quote_pdf

        for quote in queryset:
            # Recalculate estimated total
            quote.recalculate_estimated_total()
            quote.save()

            # Regenerate PDF
            generate_quote_pdf.apply_async(args=[quote.id])

        self.message_user(
            request,
            f'{queryset.count()} PDF(s) are being regenerated.',
            level=messages.SUCCESS
        )
    regenerate_pdfs.short_description = 'Regenerate PDFs (no email)'

    def get_urls(self):
        """Add custom URLs for admin actions"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:quote_id>/generate-pdf/',
                self.admin_site.admin_view(self.generate_pdf_view),
                name='quotes_quoterequest_generate_pdf',
            ),
        ]
        return custom_urls + urls

    def generate_pdf_view(self, request, quote_id):
        """Generate PDF and download it immediately"""
        from django.template.loader import render_to_string
        from weasyprint import HTML

        try:
            quote_request = QuoteRequest.objects.get(id=quote_id)
            config = SiteConfiguration.get_config()

            # Recalculate estimated total
            quote_request.recalculate_estimated_total()
            quote_request.save()

            # Render HTML template
            html_string = render_to_string('quotes/pdf/quote_pdf.html', {
                'quote_request': quote_request,
                'config': config,
            })

            # Generate PDF
            pdf_file = HTML(string=html_string).write_pdf()

            # Return as download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="quote_{quote_request.quote_number}.pdf"'

            return response

        except QuoteRequest.DoesNotExist:
            self.message_user(request, 'Quote request not found.', level=messages.ERROR)
            return redirect('admin:quotes_quoterequest_changelist')
        except Exception as e:
            self.message_user(request, f'Error generating PDF: {str(e)}', level=messages.ERROR)
            return redirect('admin:quotes_quoterequest_change', quote_id)

    def convert_to_property(self, request, queryset):
        """Convert selected quote requests to properties"""
        from listen_hear_audio.builders.models import Property, PurchasedPackage

        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one quote to convert.', level=messages.WARNING)
            return

        quote = queryset.first()

        # Check if already converted
        if quote.properties.exists():
            existing = quote.properties.first()
            url = reverse('admin:builders_property_change', args=[existing.pk])
            self.message_user(
                request,
                format_html('This quote has already been converted to property: <a href="{}">{}</a>', url, existing.name),
                level=messages.WARNING
            )
            return

        # Create property from quote
        property_name = f"{quote.contact_person} - {quote.quote_number}"

        # Build address from separate fields
        address_parts = []
        if quote.street:
            address_parts.append(quote.street)
        if quote.city:
            address_parts.append(quote.city)
        if quote.state:
            address_parts.append(quote.state)
        if quote.zip_code:
            address_parts.append(quote.zip_code)
        full_address = ', '.join(address_parts)

        property_obj = Property.objects.create(
            name=property_name,
            address=full_address,
            property_type='',  # Can be set manually later
            quote_request=quote
        )

        # Create purchased packages from quote items
        for item in quote.items.all():
            PurchasedPackage.objects.create(
                property=property_obj,
                package=item.package,
                package_name=item.package_name,
                package_description=item.package_description,
                price_snapshot=item.price_snapshot,
                quantity=item.quantity,
                status='pending'
            )

        # Redirect to property admin to add builders
        url = reverse('admin:builders_property_change', args=[property_obj.pk])
        messages.success(
            request,
            format_html('Property created successfully! <a href="{}">Click here to add builders and manage the property.</a>', url)
        )

        # Update quote status
        quote.status = 'accepted'
        quote.save()

    convert_to_property.short_description = 'Convert selected quote to property'


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'business_email', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Business Information', {
            'fields': (
                'business_name',
                'business_logo',
                'business_address',
                'business_phone',
                'business_email',
                'business_website'
            )
        }),
        ('Notifications', {
            'fields': ('notification_emails',),
            'description': 'Enter email addresses as a JSON array, e.g., ["email1@example.com", "email2@example.com"]'
        }),
        ('Email Templates', {
            'fields': (
                'customer_email_subject',
                'customer_email_message'
            )
        }),
        ('Legal', {
            'fields': ('quote_disclaimer',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the configuration
        return False