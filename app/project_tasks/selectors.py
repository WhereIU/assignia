from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from django.utils import timezone
from .constants import PriorityLevel, RiskLevel, TaskStatus

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from users.models import User
    from .models import Task
    from .permissions import ProjectTasksPermissions


def get_task_status_choices() -> list[tuple[str, str]]:
    """Return task status choices."""
    return TaskStatus.choices


def get_task_priority_choices() -> list[tuple[int, str]]:
    """Return task priority choices."""
    return PriorityLevel.choices


def get_task_risk_choices() -> list[tuple[int, str]]:
    """Return task risk choices."""
    return RiskLevel.choices


def get_form_choices_context() -> dict:
    """Return unified context."""
    return {
        "status_choices": get_task_status_choices(),
        "priority_choices": get_task_priority_choices(),
        "risk_choices": get_task_risk_choices(),
        "now": timezone.now(),
    }


def get_task_by_pk(pk: int) -> Optional[Task]:
    """Fetch a task by its primary key."""
    from .models import Task
    return Task.objects.filter(pk=pk).select_related("project", "project__owner", "creator").first()


def get_tasks_by_project(project) -> QuerySet[Task]:
    """Return base tasks queryset for a specific project."""
    from .models import Task
    return Task.objects.filter(project=project).prefetch_related("assignments__user")


def get_task_comments_context(task: Task, page_number: int | str) -> dict:
    """Return task comments context."""
    from common.selectors import get_paginated_page
    comments = task.comments.select_related("author").order_by("created_at")
    page_obj = get_paginated_page(queryset=comments, per_page=15, page=page_number)
    return {"page_obj": page_obj, "task": task}


def get_available_actions_for_task(task: Task, user: User, perms: ProjectTasksPermissions) -> dict[str, bool]:
    """Return map of allowed actions for the task based on user permissions."""
    if not user or not user.is_authenticated:
        return {
            "can_edit": False,
            "can_delete": False,
            "can_take": False,
            "can_comment": False,
            "is_assignee": False,
        }

    is_active = task.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]
    is_assignee = task.assignments.filter(user=user).exists()

    return {
        "can_edit": perms.can_manage_tasks,
        "can_delete": perms.can_manage_tasks,
        "can_take": perms.is_member and task.status == TaskStatus.NEW and not task.assignments.exists(),
        "can_comment": (is_assignee or perms.can_manage_tasks) and is_active,
        "is_assignee": is_assignee,
    }