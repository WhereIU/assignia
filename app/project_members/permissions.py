from typing import Optional

from .constants import (
    ADMIN_ROLES,
    PRIVILEGED_ROLES,
    ADMIN_MANAGEABLE_ROLES,
    REQUEST_MANAGEMENT_ROLES,
    ProjectRole,
)
from .selectors import get_membership, get_member_role, get_member_role
from project_tasks.constants import TaskStatus


def is_project_member(user, project) -> bool:
    """Check whether user is member of project."""
    return bool(get_membership(user, project))


def can_access_project(user, project) -> bool:
    """Check whether user can view project."""
    if project.is_public:
        return True
    return is_project_member(user, project)


def can_manage_project(user, project) -> bool:
    """Check whether user can manage project."""
    return get_member_role(user, project) in ADMIN_ROLES


def can_manage_directions(user, project) -> bool:
    """Check whether user can manage in directions."""
    return get_member_role(user, project) in ADMIN_ROLES


def can_manage_member(user, target_membership, project) -> bool:
    """Check whether user can change membership."""
    if not user.is_authenticated:
        return False

    member_role = get_member_role(user, project)
    if not member_role:
        return False

    if member_role == ProjectRole.OWNER:
        return True

    if member_role == ProjectRole.ADMIN:
        return target_membership.role in ADMIN_MANAGEABLE_ROLES

    return False


def can_manage_teams(user, direction) -> bool:
    """Check whether user can manage teams in direction."""
    return can_manage_directions(user, direction.project)


def can_handle_requests(user, project) -> bool:
    """Check whether user can handle project requests."""
    return get_member_role(user, project) in REQUEST_MANAGEMENT_ROLES


def can_take_task(user, task) -> bool:
    """Check whether user can take task."""
    return (
        user.is_authenticated
        and task.status == TaskStatus.NEW
        and not task.assignments.exists()
        and is_project_member(user, task.project)
    )


def can_delete_task_or_error(user, task) -> Optional[str]:
    """
    Check whether user can delete task.
    Returns None if allowed, otherwise error message.
    """
    if not is_project_member(user, task.project):
        return "Вы не участник проекта"

    role = get_member_role(user, task.project)

    if role == ProjectRole.PARTICIPANT:
        if task.creator != user:
            return "Вы не автор задачи"
        if (
            task.status not in (TaskStatus.NEW, TaskStatus.PENDING)
            or task.assignments.exists()
        ):
            return "Нельзя удалить эту задачу"
    elif role not in PRIVILEGED_ROLES:
        return "Недостаточно прав"

    return None


def is_privileged(user, project) -> bool:
    """Check whether user has privileged role."""
    return get_member_role(user, project) in PRIVILEGED_ROLES


def is_admin_or_owner(user, project) -> bool:
    """Check whether user is admin or owner."""
    return get_member_role(user, project) in ADMIN_ROLES

