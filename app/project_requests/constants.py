from django.db import models


class RequestStatus(models.TextChoices):
    PENDING = "pending", "На рассмотрении"
    REVIEWED = "reviewed", "Рассмотрен"
    DECLINED = "declined", "Отклонён"
    CONVERTED = "converted", "Преобразован в задачу"
