from django.db import models
from django.conf import settings

from projects.models import Project

from .constants import  ProjectRole


class ProjectMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=32,
        choices=ProjectRole.choices,
        default=ProjectRole.PARTICIPANT,
    )
    team = models.ForeignKey('project_teams.Team', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} в {self.project.name} как {self.get_role_display()}"
    
