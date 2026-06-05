from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from projects.models import Project
    from users.models import User

from .models import Direction


def create_direction(
    *, project: Project, user: User, name: str, description: str
) -> Direction:
    """Create new direction and return it."""
    return Direction.objects.create(
        project=project,
        created_by=user,
        name=name,
        description=description,
    )


def update_direction(*, direction: Direction, name: str, description: str) -> Direction:
    """Update existing direction's."""
    direction.name = name
    direction.description = description
    direction.save(update_fields=["name", "description"])
    return direction


def soft_delete_direction(*, direction: Direction) -> Direction:
    """Mark a direction as soft-deleted."""
    direction.is_deleted = True
    direction.save(update_fields=["is_deleted"])
    return direction


def restore_direction(*, direction: Direction) -> Direction:
    """Restore soft-deleted direction."""
    direction.is_deleted = False
    direction.save(update_fields=["is_deleted"])
    return direction


def hard_delete_direction(*, direction: Direction) -> None:
    """Permanently delete a direction."""
    direction.delete()
