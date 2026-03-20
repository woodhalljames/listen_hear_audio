from django.db.models.signals import post_save
from django.dispatch import receiver

from listen_hear_audio.users.models import User


@receiver(post_save, sender=User)
def sync_newsletter_subscription(sender, instance, **kwargs):
    """Keep the Subscriber list in sync with User.subscribe_to_newsletter."""
    from django.utils import timezone
    from listen_hear_audio.subscribers.models import Subscriber

    if instance.subscribe_to_newsletter:
        subscriber, created = Subscriber.objects.get_or_create(email=instance.email)
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
    else:
        Subscriber.objects.filter(email=instance.email, is_active=True).update(
            is_active=False,
            unsubscribed_at=timezone.now(),
        )
