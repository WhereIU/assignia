from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, Case, When, IntegerField, QuerySet

from project_members.permissions import is_project_member
from project_directions.selectors import get_directions_by_project
from project_teams.selectors import get_teams_by_project
from users.models import User

from .constants import TaskStatus, RiskLevel
from .models import Task, TaskAssignment, TaskComment

User = get_user_model()


def create_task(
    *,
    form,
    project,
    creator: User,
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


def update_task(
    *,
    task: Task,
    data: Dict[str, Any],
    assignee_ids: Optional[List[int]] = None,
) -> Task:
    """Update task fields from data and sync assignees."""
    task.name = data.get("name", task.name)
    task.status = data.get("status", task.status)
    task.priority = int(data.get("priority", task.priority))
    task.risk_chance = int(data.get("risk_chance", task.risk_chance))
    task.risk_impact = int(data.get("risk_impact", task.risk_impact))
    task.description = data.get("description", task.description)
    deadline = data.get("deadline")
    task.deadline = deadline if deadline else None
    task.save()

    if assignee_ids is not None:
        _sync_assignees(task, assignee_ids)

    return task


def delete_task(*, task: Task) -> Task:
    """Soft-delete task."""
    task.is_deleted = True
    task.save(update_fields=["is_deleted"])
    return task


def restore_task(*, task: Task) -> Task:
    """Restore soft-deleted task."""
    task.is_deleted = False
    task.save(update_fields=["is_deleted"])
    return task


def update_task_status(*, task: Task, status: TaskStatus) -> Task:
    """Update status of task."""
    task.status = status
    task.save(update_fields=["status"])
    return task


def update_task_priority(*, task: Task, priority: int) -> Task:
    """Update priority of task."""
    task.priority = priority
    task.save(update_fields=["priority"])
    return task


def update_task_risk(*, task: Task, chance: int, impact: int) -> Task:
    """Update risk chance and impact of task."""
    task.risk_chance = chance
    task.risk_impact = impact
    task.save(update_fields=["risk_chance", "risk_impact"])
    return task


def take_task(*, task: Task, user: User) -> Task:
    """Assign a user to a task and set status to in progress."""
    TaskAssignment.objects.create(task=task, user=user)
    task.status = TaskStatus.IN_PROGRESS
    task.save(update_fields=["status"])
    return task


def add_task_comment(*, task: Task, author: User, text: str) -> TaskComment:
    """Add comment to task."""
    return TaskComment.objects.create(task=task, author=author, text=text)


def assign_user_to_task(*, task: Task, user_id: int) -> Optional[str]:
    """Assign user to task.
    Returns error message on failure, or None on success."""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return "Пользователь не найден"

    if not is_project_member(user, task.project):
        return "Пользователь не участник проекта"

    TaskAssignment.objects.get_or_create(task=task, user=user)
    return None


def remove_user_from_task(*, task: Task, user_id: int) -> None:
    """Remove user from task's assignees."""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    TaskAssignment.objects.filter(task=task, user=user).delete()


def add_direction_to_task(*, task: Task, direction_id: int) -> Optional[str]:
    """Add direction to task.
    Returns error message on failure, or None on success."""
    directions = get_directions_by_project(task.project, is_deleted=False)
    try:
        direction = directions.get(pk=direction_id)
    except directions.model.DoesNotExist:
        return "Направление не найдено"
    task.directions.add(direction)
    return None


def remove_direction_from_task(*, task: Task, direction_id: int) -> None:
    """Remove direction from task."""
    directions = get_directions_by_project(task.project, is_deleted=False)
    try:
        direction = directions.get(pk=direction_id)
    except directions.model.DoesNotExist:
        return
    task.directions.remove(direction)


def add_team_to_task(*, task: Task, team_id: int) -> Optional[str]:
    """Add team to task.
    Returns error message on failure, or None on success."""
    teams = get_teams_by_project(task.project, is_deleted=False)
    try:
        team = teams.get(pk=team_id)
    except teams.model.DoesNotExist:
        return "Команда не найдена"
    task.teams.add(team)
    return None


def remove_team_from_task(*, task: Task, team_id: int) -> None:
    """Remove team from task."""
    teams = get_teams_by_project(task.project, is_deleted=False)
    try:
        team = teams.get(pk=team_id)
    except teams.model.DoesNotExist:
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
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            continue
        if is_project_member(user, task.project):
            TaskAssignment.objects.get_or_create(task=task, user=user)
