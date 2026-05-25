from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from tasks.models import Comment
from projects.models import Invitation

from .models import Notification


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return
    task = instance.task
    task_url = reverse('tasks:task_detail', kwargs={'task_pk': task.pk})

    if task.creator and task.creator != instance.author:
        Notification.objects.create(
            recipient=task.creator,
            text=f'Новый комментарий от {instance.author.username} в задаче «{task.title}»',
            url=task_url
        )
    for assignment in task.assignments.all():
        if assignment.user != instance.author and assignment.user != task.creator:
            Notification.objects.create(
                recipient=assignment.user,
                text=f'Новый комментарий от {instance.author.username} в задаче «{task.title}»',
                url=task_url
            )


@receiver(post_save, sender=Invitation)
def invitation_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.recipient,
            text=f'{instance.sender.username} приглашает вас в проект «{instance.project.name}»',
            url=reverse('projects:invitation_accept', kwargs={'invitation_pk': instance.pk})
        )
