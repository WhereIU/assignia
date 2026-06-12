from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError

from .models import ProjectMembership
from .constants import ProjectRole
from .selectors import get_default_member_role

if TYPE_CHECKING:
    from users.models import User
    from projects.models import Project


def create_membership(
    *, user: User, project: Project, role: Optional[str] = None
) -> ProjectMembership:
    """Add user as member of project."""
    if role is None:
        role = get_default_member_role()
    return ProjectMembership.objects.create(user=user, project=project, role=role)

def update_member_role(*, target_membership: ProjectMembership, new_role: str) -> None:
    """Change member's role safely."""
    if new_role not in ProjectRole.values:
        raise ValidationError("Указана несуществующая роль.")
        
    target_membership.role = new_role
    target_membership.save(update_fields=["role"])

def remove_member(*, target_membership: ProjectMembership) -> str:
    """Remove member from project and return their username."""
    username = target_membership.user.username
    target_membership.delete()
    return username
