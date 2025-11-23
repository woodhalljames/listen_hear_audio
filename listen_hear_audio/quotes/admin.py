from django.contrib import admin
from django.utils.html import format_html
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
        'pdf_link'
    ]
    inlines = [QuoteRequestItemInline]
    
    fieldsets = (
        ('Quote Information', {
            'fields': ('quote_number', 'status', 'user', 'estimated_total', 'pdf_link')
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