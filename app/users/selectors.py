from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from common.selectors import get_paginated_page

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


def get_profile_projects_context(projects_queryset, search_query: str, page_number: str) -> dict:
    """Return context for profile projects."""
    filtered_projects = filter_projects_by_search(projects_queryset, search_query.strip())
    projects_page = get_paginated_page(queryset=filtered_projects, page=page_number, per_page=6)
    
    return {
        "projects": projects_page,
        "search_query": search_query.strip(),
    }
