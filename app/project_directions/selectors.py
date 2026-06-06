from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from projects.models import Project

from .models import Direction


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
