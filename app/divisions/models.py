from django.db import models
from django.conf import settings

class Direction(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='directions')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        default_related_name = 'directions'

    def __str__(self):
        return f"{self.name} ({self.project.name})"

class Team(models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=200)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='teams')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        default_related_name = 'teams'

    def __str__(self):
        return f"{self.name} ({self.direction.name})"