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
        
        # Render HTML template
        html_string = render_to_string('quotes/pdf/quote_pdf.html', {
            'quote_request': quote_request,
            'config': config,
        })
        
        # Generate PDF from HTML
        pdf_file = HTML(string=html_string).write_pdf()
        
        # Save PDF to quote request
        filename = f'quote_{quote_request.quote_number}.pdf'
        quote_request.pdf_path.save(filename, ContentFile(pdf_file), save=True)
        
        logger.info(f'PDF generated for quote {quote_request.quote_number}')
        return True
        
    except Exception as e:
        logger.error(f'Error generating PDF for quote {quote_request_id}: {str(e)}')
        return False


@shared_task
def send_quote_emails(quote_request_id):
    """Send quote confirmation emails to customer and host"""
    try:
        quote_request = QuoteRequest.objects.get(id=quote_request_id)
        config = SiteConfiguration.get_config()
        
        # Wait for PDF to be generated (if not already)
        if not quote_request.pdf_path:
            # Retry after a short delay
            raise Exception('PDF not yet generated')
        
        # Email to customer
        customer_subject = config.customer_email_subject
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
        with quote_request.pdf_path.open('rb') as pdf:
            customer_email.attach(
                f'quote_{quote_request.quote_number}.pdf',
                pdf.read(),
                'application/pdf'
            )
        
        customer_email.send()
        logger.info(f'Customer email sent for quote {quote_request.quote_number}')
        
        # Email to host(s)
        if config.notification_emails:
            host_subject = f'New Quote Request - {quote_request.quote_number}'
            host_message = render_to_string('quotes/emails/host_email.html', {
                'quote_request': quote_request,
                'config': config,
            })
            
            host_email = EmailMessage(
                subject=host_subject,
                body=host_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=config.notification_emails,
            )
            host_email.content_subtype = 'html'
            
            # Attach PDF
            with quote_request.pdf_path.open('rb') as pdf:
                host_email.attach(
                    f'quote_{quote_request.quote_number}.pdf',
                    pdf.read(),
                    'application/pdf'
                )
            
            host_email.send()
            logger.info(f'Host email sent for quote {quote_request.quote_number}')
        
        return True
        
    except Exception as e:
        logger.error(f'Error sending emails for quote {quote_request_id}: {str(e)}')
        # Retry the task
        raise send_quote_emails.retry(exc=e, countdown=60, max_retries=3)