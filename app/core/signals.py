import os

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from project_tasks.models import TaskComment
from projects.models import Invitation

from .models import Notification


User = get_user_model()


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



@receiver(pre_save, sender=User)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Delete user avatar if it changed
    """
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).avatar
    except sender.DoesNotExist:
        return False

    new_file = instance.avatar
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(post_delete, sender=User)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Delete user avatar on user deletion.
    """
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)
