from __future__ import annotations
from typing import TYPE_CHECKING

from .models import Notification

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.contrib.auth import get_user_model
    User = get_user_model()


def get_notifications_for_user(user: User) -> QuerySet[Notification]:
    """
    Return queryset of notifications for user.
    """
    return (
        Notification.objects.filter(recipient=user)
        .order_by("-created_at")
        .prefetch_related("target_object") 
    )