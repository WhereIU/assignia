from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from tasks.models import Comment

from .models import Notification


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return

    task_pk = instance.task.pk
    task_url = reverse('tasks:detail_task', kwargs={'task_pk': task_pk})

    if instance.task.creator and instance.task.creator != instance.author:
        Notification.objects.create(
            recipient=instance.task.creator,
            text=f'Новый комментарий от {instance.author.username} в задаче «{instance.task.title}»',
            url=task_url
        )
    if instance.task.assignee and instance.task.assignee != instance.author and instance.task.assignee != instance.task.creator:
        Notification.objects.create(
            recipient=instance.task.assignee,
            text=f'Новый комментарий от {instance.author.username} в задаче «{instance.task.title}»',
            url=task_url
        )
