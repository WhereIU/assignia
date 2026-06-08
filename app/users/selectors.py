from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from .models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_user_by_username(username: str) -> Optional[User]:
    """Return user by username."""
    return User.objects.filter(username=username).first()


def filter_projects_by_search(projects_queryset: QuerySet, search_query: str) -> QuerySet:
    """Returns filtered projects by search."""
    if search_query:
        return projects_queryset.filter(name__icontains=search_query)
    return projects_queryset
