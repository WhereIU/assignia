from django.db import models
from django.conf import settings


class Direction(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='directions')
    name = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        default_related_name = 'directions'

    def __str__(self):
        return f"{self.name} ({self.project.name})"
