from django.db import models
from django.conf import settings
from django.core.validators import MaxLengthValidator

from common.models import (
    TimeStampedModel,
    SoftDeleteModel,
)
from .constants import TaskStatus, PriorityLevel, RiskLevel


class Task(TimeStampedModel, SoftDeleteModel):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=64)
    description = models.TextField(
        blank=True,
        validators=[MaxLengthValidator(1000, message="Описание задачи не должно превышать 1000 символов.")]
    )
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    priority = models.IntegerField(choices=PriorityLevel.choices, default=PriorityLevel.MEDIUM)
    risk_chance = models.IntegerField(choices=RiskLevel.choices, default=RiskLevel.LOW)
    risk_impact = models.IntegerField(choices=RiskLevel.choices, default=RiskLevel.LOW)
    status = models.CharField(max_length=16, choices=TaskStatus.choices, default=TaskStatus.NEW)
    deadline = models.DateTimeField(null=True, blank=True)
    directions = models.ManyToManyField('project_directions.Direction', blank=True, related_name='tasks')
    teams = models.ManyToManyField('project_teams.Team', blank=True, related_name='tasks')
    all_objects = models.Manager()
    objects = models.Manager()

    def __str__(self):
        return self.name

class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'user')

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
