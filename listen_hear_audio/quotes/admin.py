from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import Cart, CartItem, QuoteRequest, QuoteRequestItem, Coupon
from listen_hear_audio.core.models import SiteConfiguration


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    fields = ['package', 'quantity', 'notes', 'added_at']
    readonly_fields = ['added_at']
    autocomplete_fields = ['package']


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
    fields = ['package', 'price_snapshot', 'quantity', 'notes']
    autocomplete_fields = ['package']
    verbose_name = 'Package'
    verbose_name_plural = 'Packages'

    class Media:
        js = ('js/admin/quote_inline_autofill.js',)



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
        'finalize_link',
        'convert_property_link',
        'property_link'
    ]
    inlines = [QuoteRequestItemInline]
    actions = ['finalize_quotes', 'regenerate_pdfs', 'convert_to_property']

    fieldsets = (
        ('Quote Information', {
            'fields': ('quote_number', 'status', 'user', 'estimated_total')
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
            'fields': ('admin_notes', 'email_recipients', 'pdf_link', 'finalize_link', 'finalized_at', 'finalized_by'),
            'description': 'Set email recipients (one per line), then generate & preview the PDF before finalizing.',
        }),
        ('Property Management', {
            'fields': ('convert_property_link', 'property_link'),
            'description': 'Convert this quote into a managed property for builder coordination.',
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
        return format_html('<strong style="color: #0a0;">${}</strong>', f'{float(obj.final_total):,.2f}')
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
                '<i class="bi bi-file-pdf"></i> View Original</a>'
            )

        # Generate/Download PDF button
        generate_url = reverse('admin:quotes_quoterequest_generate_pdf', args=[obj.pk])
        buttons.append(
            f'<a href="{generate_url}" class="button" style="margin-right: 5px;">'
            '<i class="bi bi-download"></i> Generate & Download</a>'
        )

        return format_html(' '.join(buttons))
    pdf_link.short_description = 'PDF Actions'

    def finalize_link(self, obj):
        if not obj.pk:
            return "Save quote first"

        finalize_url = reverse('admin:quotes_quoterequest_finalize', args=[obj.pk])

        if obj.is_finalized():
            button_text = '🔄 Re-Finalize & Send Email'
            button_style = 'background-color: #f0ad4e; color: white;'
        else:
            button_text = '✓ Finalize & Send Email'
            button_style = 'background-color: #5cb85c; color: white;'

        return format_html(
            '<a href="{}" class="button" style="margin-right: 5px; {}">{}</a>',
            finalize_url, button_style, button_text
        )
    finalize_link.short_description = 'Finalize & Send Email'

    def convert_property_link(self, obj):
        """Button to convert quote to a managed property"""
        if not obj.pk:
            return "Save quote first"

        if obj.properties.exists():
            prop = obj.properties.first()
            url = reverse('admin:builders_property_change', args=[prop.pk])
            return format_html(
                '<span style="color: green; margin-right: 10px;">✓ Already converted</span>'
                '<a href="{}" class="button" style="background-color: var(--primary); color: white;">View Property</a>',
                url
            )

        convert_url = reverse('admin:quotes_quoterequest_convert_property', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" style="background-color: #0275d8; color: white;">'
            '🏠 Convert to Property</a>',
            convert_url
        )
    convert_property_link.short_description = 'Convert to Property'

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
    finalize_quotes.short_description = 'Finalize selected quotes & send emails'

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
                'package-info/<int:package_id>/',
                self.admin_site.admin_view(self.package_info_view),
                name='quotes_quoterequest_package_info',
            ),
            path(
                '<int:quote_id>/generate-pdf/',
                self.admin_site.admin_view(self.generate_pdf_view),
                name='quotes_quoterequest_generate_pdf',
            ),
            path(
                '<int:quote_id>/finalize/',
                self.admin_site.admin_view(self.finalize_view),
                name='quotes_quoterequest_finalize',
            ),
            path(
                '<int:quote_id>/convert-property/',
                self.admin_site.admin_view(self.convert_property_view),
                name='quotes_quoterequest_convert_property',
            ),
        ]
        return custom_urls + urls

    def package_info_view(self, request, package_id):
        """Return package details as JSON for inline auto-fill"""
        from django.http import JsonResponse
        from listen_hear_audio.products.models import Package
        try:
            package = Package.objects.get(id=package_id)
            return JsonResponse({
                'name': package.name,
                'installation_phase_value': package.installation_phase,
                'price': str(package.starting_price),
            })
        except Package.DoesNotExist:
            return JsonResponse({'error': 'Package not found'}, status=404)

    def generate_pdf_view(self, request, quote_id):
        """Generate PDF and download it immediately"""
        from django.template.loader import render_to_string
        from weasyprint import HTML

        try:
            quote_request = QuoteRequest.objects.get(id=quote_id)
            config = SiteConfiguration.load()

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

    def finalize_view(self, request, quote_id):
        """Finalize quote, generate PDF, and send emails (no property creation)"""
        from django.utils import timezone
        from celery import chain
        from listen_hear_audio.quotes.tasks import generate_quote_pdf, send_quote_emails

        try:
            quote_request = QuoteRequest.objects.get(id=quote_id)

            # Pre-populate email_recipients if empty
            if not quote_request.email_recipients:
                quote_request.email_recipients = quote_request.email

            # Always update finalized timestamp (supports re-finalize after adjustments)
            quote_request.finalized_at = timezone.now()
            quote_request.finalized_by = request.user
            quote_request.status = 'quoted'

            # Recalculate estimated total if no final total is set
            if quote_request.final_total is None:
                quote_request.recalculate_estimated_total()

            quote_request.save()

            # Regenerate PDF and send email
            task_chain = chain(
                generate_quote_pdf.si(quote_request.id),
                send_quote_emails.si(quote_request.id)
            )
            task_chain.apply_async()

            recipients = quote_request.get_email_recipients()
            self.message_user(
                request,
                f'Quote {quote_request.quote_number} finalized! PDF is being regenerated and emails will be sent to: {", ".join(recipients)}',
                level=messages.SUCCESS
            )

            return redirect('admin:quotes_quoterequest_change', quote_id)

        except QuoteRequest.DoesNotExist:
            self.message_user(request, 'Quote request not found.', level=messages.ERROR)
            return redirect('admin:quotes_quoterequest_changelist')
        except Exception as e:
            self.message_user(request, f'Error finalizing quote: {str(e)}', level=messages.ERROR)
            return redirect('admin:quotes_quoterequest_change', quote_id)

    def convert_property_view(self, request, quote_id):
        """Convert a quote request into a managed property"""
        from listen_hear_audio.builders.models import Property, PurchasedPackage

        try:
            quote = QuoteRequest.objects.get(id=quote_id)

            # Check if already converted
            if quote.properties.exists():
                existing = quote.properties.first()
                url = reverse('admin:builders_property_change', args=[existing.pk])
                self.message_user(
                    request,
                    format_html('This quote has already been converted to property: <a href="{}">{}</a>', url, existing.name),
                    level=messages.WARNING
                )
                return redirect('admin:quotes_quoterequest_change', quote_id)

            # Build property name and address
            property_name = f"{quote.contact_person} - {quote.quote_number}"
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

            # Create property
            property_obj = Property.objects.create(
                name=property_name,
                address=full_address,
                property_type='',
                quote_request=quote
            )

            # Create purchased packages from quote items
            for item in quote.items.all():
                PurchasedPackage.objects.create(
                    property=property_obj,
                    package=item.package,
                    package_name=item.package_name,
                    package_description=item.package_description,
                    installation_phase_snapshot=item.installation_phase_snapshot,
                    price_snapshot=item.price_snapshot,
                    quantity=item.quantity,
                )

            # Auto-assign builders
            assigned_builders = []
            if quote.user and quote.user.is_builder:
                property_obj.builders.add(quote.user)
                assigned_builders.append(quote.user.email)

            from listen_hear_audio.users.models import User
            if quote.email_recipients:
                for email in quote.get_email_recipients():
                    try:
                        builder_user = User.objects.get(email=email, is_builder=True)
                        if builder_user not in property_obj.builders.all():
                            property_obj.builders.add(builder_user)
                            assigned_builders.append(builder_user.email)
                    except User.DoesNotExist:
                        pass

            # Send notification email to assigned builders
            from listen_hear_audio.builders.tasks import send_property_creation_email
            if property_obj.builders.exists():
                send_property_creation_email.delay(property_obj.id)

            # Update quote status
            quote.status = 'accepted'
            quote.save()

            # Build success message
            url = reverse('admin:builders_property_change', args=[property_obj.pk])
            if assigned_builders:
                builder_msg = f' Assigned to builders: {", ".join(assigned_builders)}.'
            else:
                builder_msg = ' No builders assigned yet.'

            self.message_user(
                request,
                format_html('Property "{}" created successfully!{} <a href="{}">View Property</a>', property_name, builder_msg, url),
                level=messages.SUCCESS
            )

            return redirect('admin:quotes_quoterequest_change', quote_id)

        except QuoteRequest.DoesNotExist:
            self.message_user(request, 'Quote request not found.', level=messages.ERROR)
            return redirect('admin:quotes_quoterequest_changelist')
        except Exception as e:
            self.message_user(request, f'Error converting to property: {str(e)}', level=messages.ERROR)
            return redirect('admin:quotes_quoterequest_change', quote_id)

    def convert_to_property(self, request, queryset):
        """Bulk action: Convert selected quote to property"""
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one quote to convert.', level=messages.WARNING)
            return
        quote = queryset.first()
        return redirect(reverse('admin:quotes_quoterequest_convert_property', args=[quote.pk]))

    convert_to_property.short_description = 'Convert selected quote to property'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin for Coupon model"""
    list_display = ('code', 'discount_display', 'active', 'valid_from', 'valid_until', 'usage_display', 'created_at')
    list_filter = ('active', 'discount_type', 'created_at')
    search_fields = ('code', 'description')
    readonly_fields = ('current_uses', 'created_at', 'updated_at')

    fieldsets = (
        ('Coupon Code', {
            'fields': ('code', 'description', 'active')
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Order Amount Restrictions', {
            'fields': ('min_order_amount', 'max_order_amount'),
            'description': 'Optional: Set minimum and/or maximum order amounts for this coupon to apply (leave blank for no restrictions)'
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'current_uses'),
            'description': 'Leave max_uses blank for unlimited uses'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def discount_display(self, obj):
        """Display discount value"""
        return obj.get_discount_display()
    discount_display.short_description = 'Discount'

    def usage_display(self, obj):
        """Display usage stats"""
        if obj.max_uses:
            return f"{obj.current_uses} / {obj.max_uses}"
        return f"{obj.current_uses} / ∞"
    usage_display.short_description = 'Uses'