from django.db import models


class ProjectRole(models.TextChoices):
    OWNER = "owner", "Владелец"
    ADMIN = "admin", "Администратор"
    MANAGER = "manager", "Менеджер"
    TECH_SUPPORT = "tech_support", "Техподдержка"
    HR_ANALYST = "hr_analyst", "Кадровый аналитик"
    PARTICIPANT = "participant", "Участник"


PRIVILEGED_ROLES = (ProjectRole.MANAGER, ProjectRole.ADMIN, ProjectRole.OWNER)
ADMIN_ROLES = (ProjectRole.ADMIN, ProjectRole.OWNER)

ADMIN_MANAGEABLE_ROLES = (
    ProjectRole.MANAGER,
    ProjectRole.TECH_SUPPORT,
    ProjectRole.HR_ANALYST,
    ProjectRole.PARTICIPANT,
)

REQUEST_MANAGEMENT_ROLES = (
    ProjectRole.TECH_SUPPORT,
    ProjectRole.MANAGER,
    ProjectRole.ADMIN,
    ProjectRole.OWNER,
)