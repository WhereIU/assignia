from __future__ import annotations
from typing import TYPE_CHECKING

from django.db.models import Avg, Count, F, Q, Sum

from project_tasks.constants import TaskStatus
from project_teams.models import Team
from users.models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from projects.models import Project


def get_teams_analytics(project: Project) -> QuerySet[Team]:
    """Return teams annotated with task statistics for project."""
    base_filter = Q(tasks__project=project) & ~Q(tasks__status=TaskStatus.CANCELLED)
    return Team.objects.filter(direction__project=project).annotate(
        total_tasks=Count("tasks", filter=base_filter),
        new_tasks=Count("tasks", filter=base_filter & Q(tasks__status=TaskStatus.NEW)),
        pending_tasks=Count(
            "tasks", filter=base_filter & Q(tasks__status=TaskStatus.PENDING)
        ),
        in_progress_tasks=Count(
            "tasks", filter=base_filter & Q(tasks__status=TaskStatus.IN_PROGRESS)
        ),
        done_tasks=Count(
            "tasks", filter=base_filter & Q(tasks__status=TaskStatus.DONE)
        ),
        avg_priority=Avg("tasks__priority", filter=base_filter),
        total_risk=Sum(
            F("tasks__risk_chance") * F("tasks__risk_impact"),
            filter=base_filter,
        ),
    )


def get_participants_analytics(project: Project) -> QuerySet[User]:
    """Return participants annotated with performance metrics."""
    assign_filter = Q(task_assignments__task__project=project) & ~Q(
        task_assignments__task__status=TaskStatus.CANCELLED
    )
    return User.objects.filter(projectmembership__project=project).annotate(
        assigned_count=Count("task_assignments", filter=assign_filter),
        done_count=Count(
            "task_assignments",
            filter=assign_filter
            & Q(task_assignments__task__status=TaskStatus.DONE),
        ),
        performance_score=Sum(
            (
                F("task_assignments__task__priority")
                * (
                    1
                    + F("task_assignments__task__risk_chance")
                    * F("task_assignments__task__risk_impact")
                    / 10.0
                )
            ),
            filter=Q(
                task_assignments__task__project=project,
                task_assignments__task__status=TaskStatus.DONE,
            ),
        ),
    )