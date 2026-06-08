from __future__ import annotations
from typing import TYPE_CHECKING

from django.db.models import Avg, Count, F, Q, Sum

from project_tasks.constants import TaskStatus
from project_teams.models import Team
from users.models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from projects.models import Project


def get_teams_analytics(project: Project, search_query: str = "") -> QuerySet[Team]:
    """Return filtered teams annotated with task statistics."""
    base_filter = Q(tasks__project=project) & ~Q(tasks__status=TaskStatus.CANCELLED)
    
    queryset = Team.objects.filter(direction__project=project)
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | Q(direction__name__icontains=search_query)
        )
        
    return queryset.annotate(
        total_tasks=Count("tasks", filter=base_filter),
        new_tasks=Count("tasks", filter=base_filter & Q(tasks__status=TaskStatus.NEW)),
        pending_tasks=Count("tasks", filter=base_filter & Q(tasks__status=TaskStatus.PENDING)),
        in_progress_tasks=Count("tasks", filter=base_filter & Q(tasks__status=TaskStatus.IN_PROGRESS)),
        done_tasks=Count("tasks", filter=base_filter & Q(tasks__status=TaskStatus.DONE)),
        total_risk=Sum(
            F("tasks__risk_chance") * F("tasks__risk_impact"),
            filter=base_filter,
        ),
    )

def get_participants_analytics(project: Project, search_query: str = "", role_filter: str = "") -> QuerySet[User]:
    """Return participants of project annotated with performance metrics."""

    membership_filter = Q(projectmembership__project=project)
    
    if role_filter:
        membership_filter &= Q(projectmembership__role=role_filter)
        
    queryset = User.objects.filter(membership_filter)
    
    if search_query:
        queryset = queryset.filter(Q(username__icontains=search_query))
        
    assign_filter = Q(task_assignments__task__project=project) & ~Q(
        task_assignments__task__status=TaskStatus.CANCELLED
    )
    
    return queryset.annotate(
        assigned_count=Count(
            "task_assignments", 
            filter=assign_filter,
            distinct=True
        ),
        done_count=Count(
            "task_assignments",
            filter=assign_filter & Q(task_assignments__task__status=TaskStatus.DONE),
            distinct=True
        ),
        performance_score=Sum(
            (
                F("task_assignments__task__priority")
                * (1 + F("task_assignments__task__risk_chance") * F("task_assignments__task__risk_impact") / 10.0)
            ),
            filter=Q(
                task_assignments__task__project=project,
                task_assignments__task__status=TaskStatus.DONE,
            ),
        ),
    ).order_by('-performance_score', 'username').distinct()