from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Mark
from .tasks import calculate_report_card_aggregates

@receiver(post_save, sender=Mark)
def mark_saved_handler(sender, instance, created, **kwargs):
    """
    Trigger report card calculation when a mark is saved.
    """
    if instance.report_card_id:
        print("iam insignal")
        # Trigger async calculation
        calculate_report_card_aggregates.apply_async(
            args=[str(instance.report_card_id)],
            countdown=5,  # Small delay to handle bulk operations
            queue='calculations'
        )


@receiver(post_delete, sender=Mark)
def mark_deleted_handler(sender, instance, **kwargs):
    """
    Trigger report card calculation when a mark is deleted.
    """
    if instance.report_card_id:
        calculate_report_card_aggregates.apply_async(
            args=[str(instance.report_card_id)],
            countdown=5,
            queue='calculations'
        )