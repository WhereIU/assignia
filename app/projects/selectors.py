from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import random

from django.db.models import Q

from project_members.selectors import get_project_ids_for_user
from projects.permissions import ProjectPermissions
from project_members.permissions import ProjectMembersPermissions
from project_directions.permissions import ProjectDirectionsPermissions
from project_tasks.permissions import ProjectTasksPermissions
from project_requests.permissions import ProjectRequestsPermissions
from project_analytics.permissions import ProjectAnalyticsPermissions

from .models import Project, Invitation
from .constants import InvitationStatus

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from users.models import User


def get_recent_public_projects(limit: int = 6) -> list[Project]:
    """Return random list of public projects."""
    pks = Project.objects.filter(is_public=True).values_list("pk", flat=True)
    random_pks = random.sample(list(pks), min(len(pks), limit))
    return list(Project.objects.filter(pk__in=random_pks))


def get_pending_invitations_for_user(user: User) -> QuerySet[Invitation]:
    """Return pending invitations for user."""
    return Invitation.objects.filter(
        recipient=user, status=InvitationStatus.PENDING
    ).select_related("project")


def get_public_projects_by_user(user: User) -> QuerySet[Project]:
    """Return public projects owned by user."""
    return Project.objects.filter(owner=user, is_public=True).order_by("-created_at")


def get_contributed_projects(user: User) -> QuerySet[Project]:
    """Return public projects where user is member but aint owner."""
    user_project_ids = get_project_ids_for_user(user)
    return (
        Project.objects.filter(
            pk__in=user_project_ids,
            is_public=True,
        )
        .exclude(owner=user)
        .distinct()
        .order_by("-created_at")
    )


def get_project(username: str, slug: str) -> Optional[Project]:
    """Return project by owner and slug."""
    return Project.objects.filter(owner__username=username, slug=slug).select_related("owner").first()


def get_available_projects(user: User, query: str = "") -> QuerySet[Project]:
    """Return available projects for user."""
    if user.is_authenticated:
        private_ids = get_project_ids_for_user(user)
        projects = Project.objects.filter(Q(is_public=True) | Q(pk__in=private_ids))
    else:
        projects = Project.objects.filter(is_public=True)
        
    if query:
        from common.search import apply_project_search_filters, parse_search_query
        filters = parse_search_query(query)
        projects = apply_project_search_filters(projects, filters)
        
    return projects.distinct().order_by("-created_at")


def get_all_public_projects_of_user(user: User) -> QuerySet[Project]:
    """Return all public projects of user."""
    user_project_ids = get_project_ids_for_user(user)
    
    return Project.objects.filter(
        Q(owner=user) | Q(pk__in=user_project_ids),
        is_public=True
    ).distinct().order_by("-created_at")


def get_pending_invitations(project: Project) -> QuerySet[Invitation]:
    """Return pending invitations for project."""
    return Invitation.objects.filter(
        project=project, status=InvitationStatus.PENDING
    ).select_related("recipient")


def get_invitation_by_pk(pk: int, **filters) -> Optional[Invitation]:
    """Return invitation by primary key with optional filters."""
    return Invitation.objects.filter(pk=pk, **filters).select_related("sender", "recipient", "project", "project__owner").first()


def filter_invitations_by_search(invitations_queryset: QuerySet, search_query: str) -> QuerySet:
    """Filter invitations by search."""
    if search_query:
        return invitations_queryset.filter(recipient__username__icontains=search_query)
    return invitations_queryset

def get_invitation_status_choices() -> list[tuple[str, str]]:
    """Return all available invitation status choices."""
    return InvitationStatus.choices


def get_pending_status_value() -> str:
    """Return value for PENDING status."""
    return InvitationStatus.PENDING

def get_default_invitation_role() -> str:
    """Return default role string for new project invitations."""
    from project_members.selectors import get_default_member_role
    return get_default_member_role()


def get_project_tabs_permissions(user, project):
    """
    Aggregate all permissions for tabs.
    """
    project_perms = ProjectPermissions(user, project)
    members_perms = ProjectMembersPermissions(user, project)
    directions_perms = ProjectDirectionsPermissions(user, project)
    tasks_perms = ProjectTasksPermissions(user, project)
    requests_perms = ProjectRequestsPermissions(user, project)
    analytics_perms = ProjectAnalyticsPermissions(user, project)

    return {
        "can_view_tasks": tasks_perms.can_view_tasks,
        "can_view_requests": requests_perms.can_view_requests,
        "can_view_analytics": analytics_perms.can_view_analytics,
        "can_view_members": members_perms.can_view_members,
        "can_view_directions": directions_perms.can_view_directions,
        "can_manage_invitations": project_perms.can_manage_invitations,
        "can_manage_settings": project_perms.can_manage_settings,
        "can_manage_directions": directions_perms.can_manage_directions,
    }
