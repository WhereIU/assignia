from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from django.shortcuts import get_object_or_404

from .models import ProjectMembership

if TYPE_CHECKING:
    from users.models import User
    from projects.models import Project
    from django.db.models import QuerySet


def get_membership(user: User, project: Project) -> Optional[ProjectMembership]:
    """Return membership by user and project."""
    return ProjectMembership.objects.filter(user=user, project=project).first()


def get_membership_by_user_pk(project: Project, user_pk: int) -> ProjectMembership:
    """Return membership by project, or 404."""
    return get_object_or_404(ProjectMembership, project=project, user__pk=user_pk)


def get_project_memberships(project: Project) -> QuerySet[ProjectMembership]:
    """Return memberships by project with related user."""
    return ProjectMembership.objects.filter(project=project).select_related("user")


def get_member_role(user: User, project: Project) -> Optional[str]:
    """Return trole of user in project, or None if not exists."""
    if not user.is_authenticated:
        return None
    membership = get_membership(user, project)
    return membership.role if membership else None


def get_project_ids_for_user(user: User) -> QuerySet[int]:
    """Return queryset of project IDs where user is member."""
    return ProjectMembership.objects.filter(user=user).values_list(
        "project_id", flat=True
    )

def get_memberships_for_user(user: User) -> QuerySet[ProjectMembership]:
    """Return memberships for user."""
    return ProjectMembership.objects.filter(user=user).select_related("project")


def search_project_memberships(
    project: Project, query: str, limit: int = 10
) -> QuerySet[ProjectMembership]:
    """Return memberships filtered by username."""
    qs = get_project_memberships(project)
    if query:
        qs = qs.filter(user__username__icontains=query)[:limit]
    return qs
