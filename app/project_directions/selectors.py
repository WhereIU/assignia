from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from django.db.models import Q

from .models import Direction

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from projects.models import Project



def get_direction_by_pk(pk: int, is_deleted: bool | None = None) -> Optional[Direction]:
    """Return direction by primary key."""
    qs = Direction.objects.all()
    if is_deleted is not None:
        qs = qs.filter(is_deleted=is_deleted)
    return qs.filter(pk=pk).first()


def get_directions_by_project(project: Project, is_deleted: bool = False) -> QuerySet[Direction]:
    """Return directions for project."""
    return Direction.objects.filter(project=project, is_deleted=is_deleted).order_by(
        "-id"
    )


def filter_directions_by_search(directions_queryset: QuerySet, search_query: str) -> QuerySet:
    """Returns filtered queryset of directions"""
    if search_query:
        return directions_queryset.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    return directions_queryset