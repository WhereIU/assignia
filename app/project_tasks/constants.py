from django.db import models


class TaskStatus(models.TextChoices):
    NEW = "new", "Новая"
    PENDING = "pending", "На рассмотрении"
    IN_PROGRESS = "in_progress", "В работе"
    DONE = "done", "Выполнена"
    CANCELLED = "cancelled", "Отменена"

class RiskLevel(models.IntegerChoices):
    VERY_LOW = 1, "1"
    LOW = 2, "2"
    MEDIUM = 3, "3"
    HIGH = 4, "4"
    CRITICAL = 5, "5"

class PriorityLevel(models.IntegerChoices):
    VERY_LOW = 1, "1"
    LOW = 2, "2"
    MEDIUM = 3, "3"
    HIGH = 4, "4"
    CRITICAL = 5, "5"
