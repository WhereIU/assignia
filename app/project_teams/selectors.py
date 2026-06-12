from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from .models import Team

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from projects.models import Project
    from project_directions.models import Direction


def get_team_by_pk(pk: int, is_deleted: Optional[bool] = None) -> Optional[Team]:
    """Return team by primary key."""
    qs = Team.objects.all()
    if is_deleted is not None:
        qs = qs.filter(is_deleted=is_deleted)
    return qs.filter(pk=pk).first()


def get_teams_by_direction(direction: Direction, is_deleted: bool = False) -> QuerySet[Team]:
    """Return teams by direction."""
    return direction.teams.filter(is_deleted=is_deleted).order_by("-id")


def get_team_members(team: Team) -> QuerySet:
    """Return members by team."""
    return team.members.all().order_by("username")


def get_teams_by_project(project: Project, is_deleted: bool = False) -> QuerySet[Team]:
    """Return teams by project."""
    return Team.objects.filter(
        direction__project=project, is_deleted=is_deleted
    ).distinct()


def filter_teams_by_search(teams_queryset: QuerySet, search_query: str) -> QuerySet:
    """Filter teams by search."""
    if search_query:
        return teams_queryset.filter(name__icontains=search_query)
    return teams_queryset


def filter_team_members_by_search(queryset: QuerySet, query: str) -> QuerySet:
    """Filter team members by search."""
    if query:
        return queryset.filter(username__icontains=query)
    return queryset