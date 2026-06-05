from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from django.shortcuts import get_object_or_404

from .models import Team

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_team_by_pk(pk: int, is_deleted: Optional[bool] = None) -> Team:
    """Return team by primary key."""
    qs = Team.objects.all()
    if is_deleted is not None:
        qs = qs.filter(is_deleted=is_deleted)
    return get_object_or_404(qs, pk=pk)


def get_teams_by_direction(direction, is_deleted: bool = False) -> QuerySet[Team]:
    """Return teams by direction."""
    return direction.teams.filter(is_deleted=is_deleted).order_by("-id")


def get_team_members(team: Team) -> QuerySet:
    """Return members by team."""
    return team.members.all()


def get_teams_by_project(project, is_deleted: bool = False) -> QuerySet[Team]:
    """Return teams by project."""
    return Team.objects.filter(
        direction__project=project, is_deleted=is_deleted
    ).distinct()
