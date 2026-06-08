from django.db.models import QuerySet
from django.contrib.auth import get_user_model


User = get_user_model()


def get_notifications_for_user(user: User) -> QuerySet:
    """Return notifications for user."""
    return (
        user.notifications
        .prefetch_related("target_object", "target_object__sender", "target_object__project")
        .order_by("-created_at")
    )
