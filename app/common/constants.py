from django.db import models


class ProjectRole(models.TextChoices):
    OWNER = "owner", "Владелец"
    ADMIN = "admin", "Администратор"
    MANAGER = "manager", "Менеджер"
    TECH_SUPPORT = "tech_support", "Техподдержка"
    HR_ANALYST = "hr_analyst", "Кадровый аналитик"
    PARTICIPANT = "participant", "Участник"


class TaskStatus(models.TextChoices):
    NEW = "new", "Новая"
    PENDING = "pending", "На рассмотрении"
    IN_PROGRESS = "in_progress", "В работе"
    DONE = "done", "Выполнена"
    CANCELLED = "cancelled", "Отменена"


class RequestStatus(models.TextChoices):
    PENDING = "pending", "На рассмотрении"
    REVIEWED = "reviewed", "Рассмотрен"
    DECLINED = "declined", "Отклонён"
    CONVERTED = "converted", "Преобразован в задачу"


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    ACCEPTED = "accepted", "Принято"
    DECLINED = "declined", "Отклонено"
    CANCELLED = "cancelled", "Отменено"


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
