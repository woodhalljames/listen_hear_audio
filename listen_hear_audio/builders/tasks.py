from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import Property, PurchasedPackage
from listen_hear_audio.quotes.models import SiteConfiguration
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_property_creation_email(property_id):
    """Send email notification when a new property is created"""
    try:
        property_obj = Property.objects.get(id=property_id)
        config = SiteConfiguration.get_config()

        # Get all builders assigned to this property
        builders = property_obj.builders.all()
        if not builders.exists():
            logger.warning(f'No builders assigned to property {property_obj.name}')
            return False

        # Create list of email recipients (all builders)
        recipient_emails = [builder.email for builder in builders]

        # Render email template
        subject = f'New Property Assigned: {property_obj.name}'
        message = render_to_string('builders/emails/property_creation.html', {
            'property': property_obj,
            'config': config,
        })

        # Send email to all builders
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_emails,
        )
        email.content_subtype = 'html'
        email.send()

        logger.info(f'Property creation email sent for {property_obj.name} to {len(recipient_emails)} builder(s)')
        return True

    except Exception as e:
        logger.error(f'Error sending property creation email for property {property_id}: {str(e)}')
        return False


@shared_task
def send_date_request_email(package_id):
    """Send email notification to company when builder requests installation date"""
    try:
        package = PurchasedPackage.objects.select_related('property').get(id=package_id)
        config = SiteConfiguration.get_config()

        # Get notification emails from site configuration
        if not config.notification_emails:
            logger.warning('No notification emails configured')
            return False

        # Render email template
        subject = f'Installation Date Requested: {package.package_name} - {package.property.name}'
        message = render_to_string('builders/emails/date_request.html', {
            'package': package,
            'property': package.property,
            'config': config,
        })

        # Send email to company admins
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=config.notification_emails,
        )
        email.content_subtype = 'html'
        email.send()

        logger.info(f'Date request email sent for package {package.package_name} on property {package.property.name}')
        return True

    except Exception as e:
        logger.error(f'Error sending date request email for package {package_id}: {str(e)}')
        return False


@shared_task
def send_date_confirmation_email(package_id):
    """Send email notification to all parties when installation date is confirmed"""
    try:
        package = PurchasedPackage.objects.select_related('property').get(id=package_id)
        config = SiteConfiguration.get_config()

        # Get all builders assigned to this property
        builders = package.property.builders.all()
        if not builders.exists():
            logger.warning(f'No builders assigned to property {package.property.name}')
            return False

        # Create list of email recipients (all builders + company admins)
        recipient_emails = [builder.email for builder in builders]
        if config.notification_emails:
            recipient_emails.extend(config.notification_emails)

        # Remove duplicates
        recipient_emails = list(set(recipient_emails))

        # Render email template
        subject = f'Installation Date Confirmed: {package.package_name} - {package.property.name}'
        message = render_to_string('builders/emails/date_confirmation.html', {
            'package': package,
            'property': package.property,
            'config': config,
        })

        # Send email to all parties
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_emails,
        )
        email.content_subtype = 'html'
        email.send()

        logger.info(f'Date confirmation email sent for package {package.package_name} to {len(recipient_emails)} recipient(s)')
        return True

    except Exception as e:
        logger.error(f'Error sending date confirmation email for package {package_id}: {str(e)}')
        return False
