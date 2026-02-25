"""
Blog notification tasks with Mailgun free-tier awareness.

Strategy
--------
- BATCH_SIZE       : 20 emails per Celery task
- DAILY_SEND_LIMIT : 50 subscriber emails per day — leaves headroom for
                     transactional emails (quotes, service requests, builders)
                     within Mailgun's 100/day free-tier cap.
- Multi-day spreading: if the subscriber list exceeds 50, the remainder is
                     automatically scheduled for the following day(s) so
                     every subscriber eventually receives the notification.
- Batches within a day are staggered 5 minutes apart.

Example — 110 subscribers:
  Day 0  → batch 0 (20) at T+0 min
            batch 1 (20) at T+5 min
            batch 2 (10) at T+10 min   ← 50 sent, daily limit reached
  Day 1  → batch 3 (20) at T+24h
            batch 4 (20) at T+24h+5min
            batch 5 (10) at T+24h+10min
"""

import math
import re
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

BATCH_SIZE = 20
DAILY_SEND_LIMIT = 20
BATCH_GAP_SECONDS = 300   # 5 minutes between batches within the same day


@shared_task(bind=True, max_retries=3)
def send_blog_post_notification(self, post_id):
    """
    Orchestrator: splits active subscribers into batches of BATCH_SIZE,
    distributes across days so no more than DAILY_SEND_LIMIT go out per day,
    and schedules each batch via Celery ETA.
    """
    from listen_hear_audio.blog.models import BlogPost
    from .models import Subscriber

    try:
        post = BlogPost.objects.get(pk=post_id, published=True)
    except BlogPost.DoesNotExist:
        return f'Post {post_id} not found or not published — skipping.'

    if post.notified_at:
        return f'Post "{post.title}" already notified at {post.notified_at} — skipping.'

    subscriber_ids = list(Subscriber.active().values_list('id', flat=True))

    if not subscriber_ids:
        return 'No active subscribers — nothing sent.'

    batches = [
        subscriber_ids[i:i + BATCH_SIZE]
        for i in range(0, len(subscriber_ids), BATCH_SIZE)
    ]

    batches_per_day = math.ceil(DAILY_SEND_LIMIT / BATCH_SIZE)  # e.g. ceil(50/20) = 3
    now = timezone.now()

    for idx, batch in enumerate(batches):
        day_offset = idx // batches_per_day
        intraday_pos = idx % batches_per_day
        eta = now + timedelta(days=day_offset, seconds=intraday_pos * BATCH_GAP_SECONDS)
        send_notification_batch.apply_async(args=[post_id, batch], eta=eta)

    BlogPost.objects.filter(pk=post_id).update(notified_at=now)

    total = len(subscriber_ids)
    total_days = (len(batches) - 1) // batches_per_day + 1
    return (
        f'Scheduled {len(batches)} batch(es) for {total} subscriber(s) '
        f'across {total_days} day(s) '
        f'(≤{DAILY_SEND_LIMIT}/day, {BATCH_SIZE} per batch).'
    )


@shared_task(bind=True, max_retries=3)
def send_notification_batch(self, post_id, subscriber_ids):
    """
    Worker task — sends the notification email to one batch of subscribers.
    Retries up to 3× on transient failure with exponential back-off.
    """
    from listen_hear_audio.blog.models import BlogPost
    from .models import Subscriber

    try:
        post = BlogPost.objects.get(pk=post_id)
    except BlogPost.DoesNotExist:
        return f'Post {post_id} no longer exists — batch skipped.'

    subscribers = Subscriber.objects.filter(id__in=subscriber_ids, is_active=True)

    from listen_hear_audio.core.models import SiteConfiguration
    config = SiteConfiguration.load()
    # settings.SITE_URL takes priority (set in local.py for dev);
    # falls back to the database SiteConfiguration.website for production.
    site_url = (getattr(settings, 'SITE_URL', None) or config.website or '').rstrip('/')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', f'Listen Hear! <{config.email}>')
    post_url = f"{site_url}{post.get_absolute_url()}"
    unsubscribe_page = f"{site_url}/subscribers/unsubscribe/"

    # Rewrite relative src/href attributes in the post body to absolute URLs
    # so images render in email clients (which have no domain to resolve against).
    def make_absolute(body):
        body = re.sub(r'src="(/[^"]*)"', lambda m: f'src="{site_url}{m.group(1)}"', body)
        body = re.sub(r"src='(/[^']*)'", lambda m: f"src='{site_url}{m.group(1)}'", body)
        return body

    absolute_body = make_absolute(post.body)

    # Build absolute featured image URL once
    featured_image_url = (
        f"{site_url}{post.featured_image.url}" if post.featured_image else None
    )

    sent = 0
    for subscriber in subscribers:
        context = {
            'post': post,
            'post_body': absolute_body,
            'featured_image_url': featured_image_url,
            'post_url': post_url,
            'unsubscribe_url': unsubscribe_page,
            'site_url': site_url,
        }

        subject = f"New from Listen Hear: {post.title}"
        html_body = render_to_string('subscribers/emails/blog_notification.html', context)
        text_body = render_to_string('subscribers/emails/blog_notification.txt', context)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=[subscriber.email],
                headers={'List-Unsubscribe': f'<{unsubscribe_page}>'},
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
            sent += 1
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    return f'Batch done: {sent}/{len(subscriber_ids)} delivered.'
