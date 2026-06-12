from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from users.models import User
    from project_directions.models import Direction

from .models import Team


def create_team(*, direction: Direction, name: str) -> Team:
    """Create new team in direction."""
    return Team.objects.create(direction=direction, name=name)


def update_team(*, team: Team, name: str) -> Team:
    """Update team's name."""
    team.name = name
    team.save(update_fields=["name"])
    return team


def soft_delete_team(*, team: Team) -> Team:
    """Soft-delete team."""
    team.is_deleted = True
    team.save(update_fields=["is_deleted"])
    return team


def hard_delete_team(*, team: Team) -> None:
    """Permanently delete team."""
    team.delete()


def restore_team(*, team: Team) -> Team:
    """Restore soft-deleted team."""
    team.is_deleted = False
    team.save(update_fields=["is_deleted"])
    return team


def add_member_to_team(team: Team, user: User) -> None:
    """Add member into team."""
    team.members.add(user)


def remove_member_from_team(team: Team, user: User) -> None:
    """Remove member from team."""
    team.members.remove(user)