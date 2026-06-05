from __future__ import annotations
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

from .models import ProjectMembership
from .constants import ProjectRole


if TYPE_CHECKING:
    from users.models import User
    from projects.models import Project


def create_membership(
    *, user: User, project: Project, role: str = ProjectRole.PARTICIPANT
) -> ProjectMembership:
    """Add user as member of project."""
    return ProjectMembership.objects.create(user=user, project=project, role=role)


def update_member_role(
    *, actor_membership: ProjectMembership, target_membership: ProjectMembership, new_role: str
) -> None:
    """Change member's role.
    Raises ValidationError if not allowed."""
    if target_membership.role == ProjectRole.OWNER:
        raise ValidationError("Нельзя изменить роль владельца")
    if new_role == ProjectRole.OWNER:
        raise ValidationError("Нельзя назначить владельца через смену роли")
    if (
        actor_membership.role == ProjectRole.ADMIN
        and target_membership.role == ProjectRole.ADMIN
    ):
        raise ValidationError("Недостаточно прав")
    if new_role not in ProjectRole.values:
        raise ValidationError("Неверная роль")
    target_membership.role = new_role
    target_membership.save(update_fields=["role"])


def remove_member(
    *, actor_membership: ProjectMembership, target_membership: ProjectMembership
) -> str:
    """Remove member, returning the username.
    Raises ValidationError if not allowed."""
    if target_membership.role == ProjectRole.OWNER:
        raise ValidationError("Нельзя удалить владельца")
    if (
        actor_membership.role == ProjectRole.ADMIN
        and target_membership.role == ProjectRole.ADMIN
    ):
        raise ValidationError("Недостаточно прав")
    username = target_membership.user.username
    target_membership.delete()
    return username
