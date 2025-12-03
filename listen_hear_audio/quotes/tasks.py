from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile
from weasyprint import HTML
from .models import QuoteRequest, SiteConfiguration
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_quote_pdf(quote_request_id):
    """Generate PDF for a quote request"""
    try:
        quote_request = QuoteRequest.objects.get(id=quote_request_id)
        config = SiteConfiguration.get_config()

        logger.info(f'Starting PDF generation for quote {quote_request.quote_number}')

        # Render HTML template
        html_string = render_to_string('quotes/pdf/quote_pdf.html', {
            'quote_request': quote_request,
            'config': config,
        })

        logger.info(f'HTML template rendered for quote {quote_request.quote_number}')

        # Generate PDF from HTML
        pdf_file = HTML(string=html_string).write_pdf()

        logger.info(f'PDF file generated for quote {quote_request.quote_number}')

        # Save PDF to quote request
        filename = f'quote_{quote_request.quote_number}.pdf'
        quote_request.pdf_path.save(filename, ContentFile(pdf_file), save=True)

        logger.info(f'PDF saved successfully for quote {quote_request.quote_number}')
        return True

    except Exception as e:
        logger.error(f'Error generating PDF for quote {quote_request_id}: {str(e)}', exc_info=True)
        return False


@shared_task
def send_quote_emails(quote_request_id):
    """Send quote confirmation emails to customer and host"""
    try:
        quote_request = QuoteRequest.objects.get(id=quote_request_id)
        config = SiteConfiguration.get_config()

        logger.info(f'Starting email send for quote {quote_request.quote_number}')

        # Email to customer
        customer_subject = config.customer_email_subject
        logger.info(f'Rendering customer email template for quote {quote_request.quote_number}')

        customer_message = render_to_string('quotes/emails/customer_email.html', {
            'quote_request': quote_request,
            'config': config,
        })

        customer_email = EmailMessage(
            subject=customer_subject,
            body=customer_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[quote_request.email],
        )
        customer_email.content_subtype = 'html'

        # Attach PDF
        logger.info(f'Attaching PDF to customer email for quote {quote_request.quote_number}')
        if quote_request.pdf_path:
            with quote_request.pdf_path.open('rb') as pdf:
                customer_email.attach(
                    f'quote_{quote_request.quote_number}.pdf',
                    pdf.read(),
                    'application/pdf'
                )
        else:
            logger.warning(f'No PDF found for quote {quote_request.quote_number}')

        customer_email.send()
        logger.info(f'Customer email sent successfully to {quote_request.email} for quote {quote_request.quote_number}')
        
        # Email to host(s)
        if config.notification_emails:
            logger.info(f'Sending host emails to {config.notification_emails} for quote {quote_request.quote_number}')
            host_subject = f'New Quote Request - {quote_request.quote_number}'
            # Build site URL from settings
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

            logger.info(f'Rendering host email template for quote {quote_request.quote_number}')
            host_message = render_to_string('quotes/emails/host_email.html', {
                'quote_request': quote_request,
                'config': config,
                'site_url': site_url,
            })

            host_email = EmailMessage(
                subject=host_subject,
                body=host_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=config.notification_emails,
            )
            host_email.content_subtype = 'html'

            # Attach PDF
            logger.info(f'Attaching PDF to host email for quote {quote_request.quote_number}')
            if quote_request.pdf_path:
                with quote_request.pdf_path.open('rb') as pdf:
                    host_email.attach(
                        f'quote_{quote_request.quote_number}.pdf',
                        pdf.read(),
                        'application/pdf'
                    )
            else:
                logger.warning(f'No PDF found to attach to host email for quote {quote_request.quote_number}')

            host_email.send()
            logger.info(f'Host email sent successfully to {config.notification_emails} for quote {quote_request.quote_number}')
        else:
            logger.warning(f'No notification emails configured - skipping host email for quote {quote_request.quote_number}')

        return True

    except Exception as e:
        logger.error(f'Error sending emails for quote {quote_request_id}: {str(e)}', exc_info=True)
        return False