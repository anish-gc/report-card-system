import logging

from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    """
    Abstract base model for all models in the project.
    Provides common fields and methods like soft delete, with robust error handling.
    """

    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s_created",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s_updated",
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    # Status fields
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Status to check if the entity is active"
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]  # Default ordering

    def activate(self, user=None) -> bool:
        """

        Args:
            user: The user performing the activation.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            

            self.is_active = True

            if user:
                self.updated_by = user

            self.save(update_fields=["is_active", "updated_by", "updated_at"])
            logger.info(
                f"{self.__class__.__name__} (id={self.id}) activated by user_id={getattr(user, 'id', None)}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error activating {self.__class__.__name__} (id={self.id}): {e}"
            )
            return False

    def deactivate(self, user=None) -> bool:
        """

        Args:
            user: The user performing the deactivation.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            

            self.is_active = False

            if user:
                self.updated_by = user

            self.save(update_fields=["is_active", "updated_by", "updated_at"])
            logger.info(
                f"{self.__class__.__name__} (id={self.id}) deactivated by user_id={getattr(user, 'id', None)}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error deactivating {self.__class__.__name__} (id={self.id}): {e}"
            )
            return False
