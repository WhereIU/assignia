from django.db import models
from django.conf import settings


class TaskRequest(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='requests')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=16, choices=[('pending', 'На рассмотрении'), ('reviewed', 'Рассмотрен'), ('declined', 'Отклонён'), ('converted', 'Преобразован в задачу')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class RequestComment(models.Model):
    request = models.ForeignKey(TaskRequest, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Сообщение от {self.author.username} в запросе #{self.request.pk}"
