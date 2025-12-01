from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
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
    extra = 0
    readonly_fields = ['package', 'package_name', 'price_snapshot', 'quantity', 'notes', 'subtotal_display']
    fields = ['package_name', 'quantity', 'price_snapshot', 'subtotal_display', 'notes']
    can_delete = False
    
    def subtotal_display(self, obj):
        if obj.price_snapshot is None:
            return format_html('<span style="color: #999;">Price not set</span>')
        return f"${obj.get_subtotal():,.2f}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = [
        'quote_number',
        'contact_person',
        'email',
        'status',
        'estimated_total_display',
        'total_items_display',
        'property_status',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['quote_number', 'contact_person', 'email', 'phone']
    readonly_fields = [
        'quote_number',
        'user',
        'estimated_total',
        'created_at',
        'updated_at',
        'pdf_link',
        'property_link'
    ]
    inlines = [QuoteRequestItemInline]
    actions = ['convert_to_property']

    fieldsets = (
        ('Quote Information', {
            'fields': ('quote_number', 'status', 'user', 'estimated_total', 'pdf_link', 'property_link')
        }),
        ('Customer Contact', {
            'fields': ('contact_person', 'email', 'phone', 'website')
        }),
        ('Location', {
            'fields': ('address', 'zip_code')
        }),
        ('Additional Information', {
            'fields': ('notes',)
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
    estimated_total_display.short_description = 'Estimated Total'
    estimated_total_display.admin_order_field = 'estimated_total'

    def total_items_display(self, obj):
        return obj.get_total_items()
    total_items_display.short_description = 'Items'

    def pdf_link(self, obj):
        if obj.pdf_path:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.pdf_path.url)
        return "No PDF generated"
    pdf_link.short_description = 'Quote PDF'

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

        property_obj = Property.objects.create(
            name=property_name,
            address=quote.address,
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