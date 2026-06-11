from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from django.utils import timezone
from django.urls import reverse

from common.selectors import get_paginated_page

from .constants import PriorityLevel, RiskLevel, TaskStatus
from .models import Task, TaskComment

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from users.models import User
    from projects.models import Project


def get_task_by_pk(pk: int) -> Optional[Task]:
    """Return task by primary key."""
    return Task.objects.select_related("project").filter(pk=pk).first()


def get_tasks_by_project(project: Project) -> QuerySet[Task]:
    """Return non-deleted tasks for project."""
    return Task.objects.filter(project=project, is_deleted=False)


def get_task_comments(task: Task) -> QuerySet[TaskComment]:
    """Return comments by task."""
    return task.comments.order_by("-created_at")


def get_tasks_assigned_to_user(user: User) -> QuerySet[Task]:
    """Return non‑deleted tasks assigned by user."""
    return Task.objects.filter(assignments__user=user, is_deleted=False)


def get_available_tasks_for_projects(project_ids: list[int]) -> QuerySet[Task]:
    """Return non‑deleted tasks for project IDS."""
    return Task.objects.filter(
        project__in=project_ids,
        status=TaskStatus.NEW,
        assignments__isnull=True,
        is_deleted=False,
    )


def get_form_choices_context() -> dict:
    return {
        "status_choices": TaskStatus.choices,
        "priority_choices": PriorityLevel.choices,
        "risk_choices": RiskLevel.choices,
        "now": timezone.now(),
    }


def get_task_comments_context(task, page_number=1) -> dict:
    comments_queryset = get_task_comments(task).order_by("-created_at")
    page_obj = get_paginated_page(queryset=comments_queryset, page=page_number, per_page=10)
    
    fixed_path = reverse("project_tasks:task_detail", kwargs={"task_pk": task.pk})
    
    return {
        "task": task,
        "comments": page_obj.object_list,
        "page_obj": page_obj,
        "fixed_path": fixed_path,
    }

def is_user_assigned_to_task(task: Task, user: User) -> bool:
    """Return True if user is assigned to the task."""
    if not user.is_authenticated:
        return False
    return task.assignments.filter(user=user).exists()