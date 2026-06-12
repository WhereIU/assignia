from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Adds created_at and updated_at fields.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Adds soft delete support.
    """
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Deleted",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Deleted at",
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()

        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None

        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )
