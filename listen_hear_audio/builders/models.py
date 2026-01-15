from django.db import models
from django.conf import settings
from django.urls import reverse


class Property(models.Model):
    """Property/project that builders manage"""

    name = models.CharField(max_length=200)
    address = models.TextField()
    property_type = models.CharField(max_length=100, blank=True)
    builders = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='managed_properties',
        limit_choices_to={'is_builder': True},
    )
    quote_request = models.ForeignKey(
        'quotes.QuoteRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} - {self.address[:50]}"

    def get_absolute_url(self):
        return reverse('builders:property_detail', kwargs={'pk': self.pk})

    def get_phase_summary(self):
        """Get summary of phase statuses"""
        phases = self.phase_installations.all()
        return {
            'total': phases.count(),
            'pending': phases.filter(status='pending').count(),
            'requested': phases.filter(status='requested').count(),
            'scheduled': phases.filter(status='scheduled').count(),
            'in_progress': phases.filter(status='in_progress').count(),
            'completed': phases.filter(status='completed').count(),
        }


class PhaseInstallation(models.Model):
    """Installation schedule for a construction phase - groups all packages in that phase"""

    PHASE_CHOICES = [
        ('framing', 'Framing'),
        ('rough_ins', 'Rough-Ins'),
        ('insulation_drywall', 'Insulation & Drywall'),
        ('trim_finishes', 'Trim & Finishes'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('requested', 'Date Requested'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='phase_installations'
    )
    phase = models.CharField(max_length=50, choices=PHASE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Requested dates from builder
    requested_date = models.DateField(null=True, blank=True)
    alternate_dates = models.JSONField(default=list, blank=True)
    builder_notes = models.TextField(blank=True)

    # Confirmed dates from admin
    confirmed_date = models.DateField(null=True, blank=True)
    estimated_end_date = models.DateField(null=True, blank=True)
    company_notes = models.TextField(blank=True)

    completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Phase Installation'
        verbose_name_plural = 'Phase Installations'
        ordering = ['phase']
        unique_together = ['property', 'phase']

    def __str__(self):
        return f"{self.property.name} - {self.get_phase_display()}"

    def get_packages(self):
        """Get all packages in this phase for this property"""
        return self.property.packages.filter(installation_phase_snapshot=self.phase)

    def package_count(self):
        return self.get_packages().count()

    def get_alternate_dates_display(self):
        """Return formatted alternate dates"""
        if not self.alternate_dates:
            return "-"
        from datetime import datetime
        dates = []
        for date_str in self.alternate_dates:
            try:
                d = datetime.strptime(date_str, '%Y-%m-%d').date()
                dates.append(d.strftime('%m/%d/%Y'))
            except (ValueError, TypeError):
                pass
        return ", ".join(dates) if dates else "-"

    def get_confirmed_dates_display(self):
        """Return formatted confirmed date range"""
        if not self.confirmed_date:
            return "-"
        if self.estimated_end_date and self.estimated_end_date != self.confirmed_date:
            return f"{self.confirmed_date.strftime('%m/%d/%Y')} - {self.estimated_end_date.strftime('%m/%d/%Y')}"
        return self.confirmed_date.strftime('%m/%d/%Y')


class PurchasedPackage(models.Model):
    """Package assigned to a property for installation"""

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='packages'
    )
    package = models.ForeignKey(
        'products.Package',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Snapshot of package details at purchase
    category_snapshot = models.CharField(max_length=200, blank=True)
    package_name = models.CharField(max_length=200)
    package_description = models.TextField(blank=True)
    installation_phase_snapshot = models.CharField(max_length=50, blank=True)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Purchased Package'
        verbose_name_plural = 'Purchased Packages'
        ordering = ['installation_phase_snapshot', 'package_name']

    def __str__(self):
        return f"{self.package_name} - {self.property.name}"

    def get_subtotal(self):
        if self.price_snapshot:
            return self.price_snapshot * self.quantity
        return 0

    def save(self, *args, **kwargs):
        """Auto-populate snapshot fields from package"""
        if self.package:
            if not self.installation_phase_snapshot:
                self.installation_phase_snapshot = self.package.installation_phase
            if not self.category_snapshot and self.package.category:
                self.category_snapshot = self.package.category.name
        super().save(*args, **kwargs)

    def get_phase_installation(self):
        """Get the PhaseInstallation for this package's phase"""
        return PhaseInstallation.objects.filter(
            property=self.property,
            phase=self.installation_phase_snapshot
        ).first()


class PropertyNote(models.Model):
    """Activity notes for properties"""

    NOTE_TYPE_CHOICES = [
        ('general', 'General'),
        ('date_request', 'Date Request'),
        ('date_confirmation', 'Date Confirmed'),
        ('status_change', 'Status Change'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    phase_installation = models.ForeignKey(
        PhaseInstallation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    note_type = models.CharField(max_length=30, choices=NOTE_TYPE_CHOICES)
    message = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Property Note'
        verbose_name_plural = 'Property Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_note_type_display()} - {self.property.name}"
