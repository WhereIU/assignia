from django.db import models
from django.conf import settings
from django.utils.text import slugify

from project_members.constants import ProjectRole
from common.models import TimeStampedModel

from .constants import InvitationStatus


class Project(TimeStampedModel):
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    is_public = models.BooleanField(default=False)
    options = models.JSONField(default=dict, blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'slug'], name='unique_owner_slug')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Invitation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invitations')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_invitations')
    status = models.CharField(max_length=16, choices=InvitationStatus.choices, default=InvitationStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(
        max_length=32, 
        choices=ProjectRole.choices, 
        default=ProjectRole.PARTICIPANT
    )
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username} ({self.project.name})"
