from django.db import models

class ProjectRole(models.TextChoices):
    OWNER = "owner", "Владелец"
    ADMIN = "admin", "Администратор"
    MANAGER = "manager", "Менеджер"
    HR_ANALYST = "hr_analyst", "Кадровый аналитик"
    TECH_SUPPORT = "tech_support", "Техподдержка"
    PARTICIPANT = "participant", "Участник"

ROLE_WEIGHTS = {
    ProjectRole.OWNER: 60,
    ProjectRole.ADMIN: 50,
    ProjectRole.MANAGER: 40,
    ProjectRole.HR_ANALYST: 30,
    ProjectRole.TECH_SUPPORT: 20,
    ProjectRole.PARTICIPANT: 10,
}
