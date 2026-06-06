from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from project_tasks.models import TaskComment
from projects.models import Invitation

from .models import Notification


@receiver(post_save, sender=Invitation)
def invitation_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.recipient,
            text=f'Пользователь {instance.sender.username} пригласил вас в проект «{instance.project.name}»',
            target_object=instance
        )


@receiver(post_save, sender=TaskComment)
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return
    task = instance.task

    recipients = set()
    if task.creator and task.creator != instance.author:
        recipients.add(task.creator)
    for assignment in task.assignments.all():
        if assignment.user != instance.author and assignment.user != task.creator:
            recipients.add(assignment.user)

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            text=f'Новый комментарий от {instance.author.username} в задаче «{task.title}»',
            target_object=instance
        )
