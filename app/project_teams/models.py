from django.db import models
from django.conf import settings

from common.models import TimeStampedModel, SoftDeleteModel
from project_directions.models import Direction


class Team(TimeStampedModel, SoftDeleteModel):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=32)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='teams')

    class Meta:
        default_related_name = 'teams'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.direction.name})"
