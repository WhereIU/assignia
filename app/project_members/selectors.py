from __future__ import annotations
from typing import Optional, TYPE_CHECKING, List, Dict

from .models import ProjectMembership
from .constants import ProjectRole

if TYPE_CHECKING:
    from users.models import User
    from projects.models import Project
    from django.db.models import QuerySet
    from .permissions import ProjectMembersPermissions


def get_default_member_role() -> str:
    """Return the default fallback role string for new members."""
    return ProjectRole.PARTICIPANT.value


def get_membership(user: User, project: Project) -> Optional[ProjectMembership]:
    """Return membership by user and project."""
    if user is None or not user.is_authenticated:
        return None
    return ProjectMembership.objects.filter(user=user, project=project).select_related("user").first()


def get_memberships_for_user(user: User) -> QuerySet[ProjectMembership]:
    """Return memberships for user."""
    return ProjectMembership.objects.filter(user=user).select_related("project")


def get_membership_by_user_pk(project: Project, user_pk: int) -> Optional[ProjectMembership]:
    """Return membership by project and user PK."""
    return ProjectMembership.objects.filter(project=project, user__pk=user_pk).select_related("user").first()


def get_project_memberships(project: Project) -> QuerySet[ProjectMembership]:
    """Return all memberships for a project."""
    return ProjectMembership.objects.filter(project=project).select_related("user").order_by("user__username")


def get_project_ids_for_user(user: User) -> QuerySet[int]:
    """Return queryset of project IDs where user is member."""
    return ProjectMembership.objects.filter(user=user).values_list("project_id", flat=True)


def search_project_memberships(project: Project, query: str) -> QuerySet[ProjectMembership]:
    """Filter project memberships by query."""
    qs = get_project_memberships(project)
    if query:
        qs = qs.filter(user__username__icontains=query)
    return qs


def get_assignable_roles_for_user(perms: ProjectMembersPermissions) -> List[Dict[str, str]]:
    """Return list of roles that the current user has permission to assign."""
    return [
        {"value": role_value, "label": role_label}
        for role_value, role_label in ProjectRole.choices
        if perms.can_add_target_role(role_value)
    ]
