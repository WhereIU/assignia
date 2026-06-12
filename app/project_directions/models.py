from django.core.validators import MaxLengthValidator
from django.db import models
from django.conf import settings

from common.models import SoftDeleteModel

class Direction(SoftDeleteModel):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='directions')
    name = models.CharField(max_length=32)
    description = models.TextField(
        blank=True, 
        validators=[MaxLengthValidator(64, message="Описание не должно превышать 64 символа.")]
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        default_related_name = 'directions'

    def __str__(self):
        return f"{self.name} ({self.project.name})"
