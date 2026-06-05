from __future__ import annotations
from typing import TYPE_CHECKING

from django.shortcuts import get_object_or_404

from project_tasks.constants import TaskStatus

from .models import Task, TaskComment

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from users.models import User


def get_task_by_pk(pk: int) -> Task:
    """Return task by primary key, or 404."""
    return get_object_or_404(Task.objects.select_related("project"), pk=pk)


def get_tasks_by_project(project) -> QuerySet[Task]:
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
