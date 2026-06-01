from django.db import models
from django.conf import settings

from project_directions.models import Direction


class Team(models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=32)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='teams')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        default_related_name = 'teams'

    def __str__(self):
        return f"{self.name} ({self.direction.name})"
