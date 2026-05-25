from django.db import models
from django.conf import settings

from projects.models import Project, Direction, Team


class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('pending', 'На рассмотрении'),
        ('in_progress', 'В работе'),
        ('done', 'Выполнена'),
        ('cancelled', 'Отменена'),
    ]
    PRIORITY_CHOICES = [(i, str(i)) for i in range(1, 6)]
    RISK_CHOICES = [(i, str(i)) for i in range(1, 6)]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3)
    risk_chance = models.IntegerField(choices=RISK_CHOICES, default=1)
    risk_impact = models.IntegerField(choices=RISK_CHOICES, default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    deadline = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    directions = models.ManyToManyField(Direction, blank=True, related_name='tasks')
    teams = models.ManyToManyField(Team, blank=True, related_name='tasks')

    def __str__(self):
        return self.title

class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'user')

class TaskRequest(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requests')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[('pending', 'На рассмотрении'), ('reviewed', 'Рассмотрен'), ('converted', 'Преобразован в задачу')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class RequestMessage(models.Model):
    request = models.ForeignKey(TaskRequest, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Сообщение от {self.author.username} в запросе #{self.request.pk}"

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
