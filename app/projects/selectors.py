from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import random

from django.db.models import Q

from project_members.selectors import get_project_ids_for_user

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
