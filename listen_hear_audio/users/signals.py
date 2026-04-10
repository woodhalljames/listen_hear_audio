from django.db.models.signals import post_save
from django.dispatch import receiver

from listen_hear_audio.users.models import User


@receiver(post_save, sender=User)
def sync_newsletter_subscription(sender, instance, created, update_fields, **kwargs):
    """Keep the Subscriber list in sync with User.subscribe_to_newsletter.

    Guards:
    - Skips the initial allauth user creation save (created=True, default False) to
      avoid briefly deactivating a pre-existing Subscriber with the same email.
    - Skips any save where subscribe_to_newsletter wasn't in the updated fields,
      preventing unnecessary subscriber churn on unrelated profile saves.
    """
    from django.utils import timezone
    from listen_hear_audio.subscribers.models import Subscriber

    # Brand-new user who didn't opt in — nothing to sync yet.
    if created and not instance.subscribe_to_newsletter:
        return

    # Partial save that didn't touch subscribe_to_newsletter — skip.
    if not created and update_fields is not None and 'subscribe_to_newsletter' not in update_fields:
        return

    if instance.subscribe_to_newsletter:
        subscriber, sub_created = Subscriber.objects.get_or_create(email=instance.email)
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
    else:
        Subscriber.objects.filter(email=instance.email, is_active=True).update(
            is_active=False,
            unsubscribed_at=timezone.now(),
        )
