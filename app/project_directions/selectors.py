from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from .models import Direction


def get_direction_by_pk(pk: int, is_deleted: bool | None = None) -> Direction:
    """Return direction by primary key,
    Raises Http404 if not found."""
    qs = Direction.objects.all()
    if is_deleted is not None:
        qs = qs.filter(is_deleted=is_deleted)
    return get_object_or_404(qs, pk=pk)


def get_directions_by_project(project, is_deleted=False) -> QuerySet[Direction]:
    """Return directions for project."""
    return Direction.objects.filter(project=project, is_deleted=is_deleted).order_by(
        "-id"
    )
