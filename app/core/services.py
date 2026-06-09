from __future__ import annotations
from typing import TYPE_CHECKING

from .models import Notification

if TYPE_CHECKING:
    from users.models import User
    from typing import Sequence


def create_notification(recipient, text, target_object=None):
    return Notification.objects.create(
        recipient=recipient,
        text=text,
        target_object=target_object
    )


def mark_notifications_as_read(user: User, notification_ids: Sequence[int]) -> int:
    """
    Marks list of notifications as read, returns count.
    """
    if not notification_ids:
        return 0
        
    return user.notifications.filter(id__in=notification_ids).update(is_read=True)