from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from .models import ProjectMembership

if TYPE_CHECKING:
    from users.models import User
    from projects.models import Project
    from django.db.models import QuerySet


def get_membership(user: User, project: Project) -> Optional[ProjectMembership]:
    """Return membership by user and project."""
    if not user.is_authenticated:
        return None
    return ProjectMembership.objects.filter(user=user, project=project).select_related("user").first()


def get_membership_by_user_pk(project: Project, user_pk: int) -> Optional[ProjectMembership]:
    """Return membership by project and user PK."""
    return ProjectMembership.objects.filter(project=project, user__pk=user_pk).select_related("user").first()


def get_project_memberships(project: Project) -> QuerySet[ProjectMembership]:
    """Return all memberships for a project."""
    return ProjectMembership.objects.filter(project=project).select_related("user").order_by("user__username")


def get_member_role(user: User, project: Project) -> Optional[str]:
    """Return the role of a member in a project."""
    membership = get_membership(user, project)
    return membership.role if membership else None


def search_project_memberships(project: Project, query: str) -> QuerySet[ProjectMembership]:
    """Filter project memberships by query."""
    qs = get_project_memberships(project)
    if query:
        qs = qs.filter(user__username__icontains=query)
    return qs
