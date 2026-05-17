from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment, Notification

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        if instance.task.creator and instance.task.creator != instance.author:
            Notification.objects.create(
                recipient=instance.task.creator,
                text=f'Новый комментарий от {instance.author.first_name or instance.author.username} в задаче «{instance.task.title}»',
                url=f'/tasks/{instance.task.pk}/'
            )

        if instance.task.assignee and instance.task.assignee != instance.author and instance.task.assignee != instance.task.creator:
            Notification.objects.create(
                recipient=instance.task.assignee,
                text=f'Новый комментарий от {instance.author.first_name or instance.author.username} в задаче «{instance.task.title}»',
                url=f'/tasks/{instance.task.pk}/'
            )