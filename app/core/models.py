from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    text = models.CharField(max_length=512)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Для {self.recipient.username}: {self.text[:30]}"

    @property
    def target_url(self) -> str:
        """If have url, return it, else return '#'"""
        if self.target_object and hasattr(self.target_object, 'get_absolute_url'):
            return self.target_object.get_absolute_url()
        return '#'
