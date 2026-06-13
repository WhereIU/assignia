from typing import List, Optional

from django.db import transaction
from django.db.models import Q, Case, When, IntegerField, QuerySet

from project_directions.selectors import get_directions_by_project
from project_teams.selectors import get_teams_by_project
from users.selectors import get_user_by_pk

from .permissions import ProjectTasksPermissions
from .constants import TaskStatus, RiskLevel, PriorityLevel
from .models import Task, TaskAssignment, TaskComment


def create_task(
    *,
    form,
    project,
    creator,
    assignee_ids: Optional[List[int]] = None,
) -> Task:
    """Save new task from form and sync assignees."""
    task = form.save(commit=False)
    task.project = project
    task.creator = creator
    task.save()

    if assignee_ids:
        _sync_assignees(task, assignee_ids)

    return task


def delete_task(*, task: Task) -> None:
    """Delete task."""
    task.delete()


def take_task(*, task: Task, user) -> Task:
    """Assign a user to a task and set status to in progress."""
    TaskAssignment.objects.get_or_create(task=task, user=user)
    task.status = TaskStatus.IN_PROGRESS
    task.save(update_fields=["status"])
    return task


def add_task_comment(*, task: Task, author, text: str) -> TaskComment:
    """Add comment to task."""
    return TaskComment.objects.create(task=task, author=author, text=text)


def assign_user_to_task(*, task: Task, user_id: int) -> Optional[str]:
    """Assign user to task. Returns error message on failure, or None on success."""
    user = get_user_by_pk(user_id)
    if not user:
        return "Пользователь не найден"

    perms = ProjectTasksPermissions(user, task.project)
    if not perms.is_member:
        return "Пользователь не участник проекта"

    TaskAssignment.objects.get_or_create(task=task, user=user)
    return None


def remove_user_from_task(*, task: Task, user_id: int) -> None:
    """Remove user from task's assignees."""
    user = get_user_by_pk(user_id)
    if not user:
        return
    TaskAssignment.objects.filter(task=task, user=user).delete()


def add_direction_to_task(*, task: Task, direction_id: int) -> Optional[str]:
    """Add direction to task."""
    directions = get_directions_by_project(task.project, is_deleted=False)
    direction = directions.filter(pk=direction_id).first()
    if not direction:
        return "Направление не найдено"
    task.directions.add(direction)
    return None


def remove_direction_from_task(*, task: Task, direction_id: int) -> None:
    """Remove direction from task."""
    directions = get_directions_by_project(task.project, is_deleted=False)
    direction = directions.filter(pk=direction_id).first()
    if not direction:
        return
    task.directions.remove(direction)


def add_team_to_task(*, task: Task, team_id: int) -> Optional[str]:
    """Add team to task."""
    teams = get_teams_by_project(task.project, is_deleted=False)
    team = teams.filter(pk=team_id).first()
    if not team:
        return "Команда не найдена"
    task.teams.add(team)
    return None


def remove_team_from_task(*, task: Task, team_id: int) -> None:
    """Remove team from task."""
    teams = get_teams_by_project(task.project, is_deleted=False)
    team = teams.filter(pk=team_id).first()
    if not team:
        return
    task.teams.remove(team)


def apply_tasks_filters(
    queryset: QuerySet[Task],
    filters: dict,
) -> QuerySet[Task]:
    """Apply filtering, annotation and ordering to task queryset."""
    status = filters.get("status", "")
    priority = filters.get("priority", "")
    risk = filters.get("risk", "")
    query = filters.get("q", "")

    if status:
        queryset = queryset.filter(status=status)
    if priority:
        queryset = queryset.filter(priority=int(priority))
    if risk == "high":
        queryset = queryset.filter(
            Q(risk_chance__gte=RiskLevel.HIGH) | Q(risk_impact__gte=RiskLevel.HIGH)
        )
    elif risk == "low":
        queryset = queryset.filter(
            risk_chance__lte=RiskLevel.LOW, risk_impact__lte=RiskLevel.LOW
        )
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    active_statuses = [TaskStatus.NEW, TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
    queryset = queryset.annotate(
        is_available=Case(
            When(assignments__isnull=True, then=1),
            default=0,
            output_field=IntegerField(),
        ),
        status_group=Case(
            When(status__in=active_statuses, then=1),
            default=2,
            output_field=IntegerField(),
        ),
    ).order_by("-is_available", "status_group", "-priority", "-created_at")

    return queryset


def _sync_assignees(task: Task, assignee_ids: List[int]) -> None:
    """Replace current assignees with the provided list of user IDs."""
    task.assignments.exclude(user__pk__in=assignee_ids).delete()
    for user_id in assignee_ids:
        user = get_user_by_pk(user_id)
        if not user:
            continue
        perms = ProjectTasksPermissions(user, task.project)
        if perms.is_member:
            TaskAssignment.objects.get_or_create(task=task, user=user)


@transaction.atomic
def update_task(task: Task, **data) -> None:
    """Update task fields from provided data."""
    if 'name' in data:
        task.name = data.get('name')
    if 'description' in data:
        task.description = data.get('description')
        
    if 'deadline' in data:
        task.deadline = data.get('deadline') or None

    if 'status' in data:
        new_status = data.get('status')
        if new_status in TaskStatus.values:
            task.status = new_status

    if 'priority' in data and data.get('priority'):
        try:
            new_priority = int(data.get('priority'))
            if new_priority in PriorityLevel.values:
                task.priority = new_priority
        except (TypeError, ValueError):
            pass

    if 'risk_chance' in data:
        try:
            new_chance = int(data.get('risk_chance'))
            if new_chance in RiskLevel.values:
                task.risk_chance = new_chance
        except (TypeError, ValueError):
            pass

    if 'risk_impact' in data:
        try:
            new_impact = int(data.get('risk_impact'))
            if new_impact in RiskLevel.values:
                task.risk_impact = new_impact
        except (TypeError, ValueError):
            pass

    task.save()
