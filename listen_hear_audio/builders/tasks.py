from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import Property, PhaseInstallation
from listen_hear_audio.core.models import SiteConfiguration
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_property_creation_email(property_id):
    """Send email when a new property is created"""
    try:
        property_obj = Property.objects.get(id=property_id)
        config = SiteConfiguration.load()

        builders = property_obj.builders.all()
        if not builders.exists():
            logger.warning(f'No builders assigned to property {property_obj.name}')
            return False

        recipient_emails = [builder.email for builder in builders]

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

        subject = f'New Property Assigned: {property_obj.name}'
        message = render_to_string('builders/emails/property_creation.html', {
            'property': property_obj,
            'config': config,
            'site_url': site_url,
            'admin_url': admin_url,
        })

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_emails,
        )
        email.content_subtype = 'html'
        email.send()

        logger.info(f'Property creation email sent for {property_obj.name}')
        return True

    except Exception as e:
        logger.error(f'Error sending property creation email: {str(e)}')
        return False


@shared_task
def send_date_request_email(phase_id):
    """Send email to admin when builder requests phase installation date"""
    try:
        phase = PhaseInstallation.objects.select_related('property').get(id=phase_id)
        config = SiteConfiguration.load()

        if not config.notification_emails:
            logger.warning('No notification emails configured')
            return False

        packages = phase.get_packages()

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

        subject = f'Install Date Requested: {phase.get_phase_display()} - {phase.property.name}'
        message = render_to_string('builders/emails/date_request.html', {
            'phase': phase,
            'property': phase.property,
            'packages': packages,
            'config': config,
            'site_url': site_url,
            'admin_url': admin_url,
        })

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=config.notification_emails,
        )
        email.content_subtype = 'html'
        email.send()

        logger.info(f'Date request email sent for {phase.get_phase_display()} on {phase.property.name}')
        return True

    except Exception as e:
        logger.error(f'Error sending date request email: {str(e)}')
        return False


@shared_task
def send_date_confirmation_email(phase_id):
    """Send email to builders when phase installation date is confirmed"""
    try:
        phase = PhaseInstallation.objects.select_related('property').get(id=phase_id)
        config = SiteConfiguration.load()

        builders = phase.property.builders.all()
        if not builders.exists():
            logger.warning(f'No builders assigned to property {phase.property.name}')
            return False

        # Send to builders + admin
        recipient_emails = [builder.email for builder in builders]
        if config.notification_emails:
            recipient_emails.extend(config.notification_emails)
        recipient_emails = list(set(recipient_emails))

        packages = phase.get_packages()

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

        subject = f'Install Date Confirmed: {phase.get_phase_display()} - {phase.property.name}'
        message = render_to_string('builders/emails/date_confirmation.html', {
            'phase': phase,
            'property': phase.property,
            'packages': packages,
            'config': config,
            'site_url': site_url,
            'admin_url': admin_url,
        })

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_emails,
        )
        email.content_subtype = 'html'
        email.send()

        logger.info(f'Date confirmation email sent for {phase.get_phase_display()}')
        return True

    except Exception as e:
        logger.error(f'Error sending date confirmation email: {str(e)}')
        return False
