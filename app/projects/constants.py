from django.db import models


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    ACCEPTED = "accepted", "Принято"
    DECLINED = "declined", "Отклонено"
    CANCELLED = "cancelled", "Отменено"
