
from .models import Notification


def create_notification(recipient, text, url=None):
    return Notification.objects.create(
        recipient=recipient,
        text=text,
        url=url
    )
