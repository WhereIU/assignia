from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from django.db.models import Q

from project_members.permissions import can_handle_requests
from project_requests.constants import RequestStatus

from .models import RequestComment, TaskRequest

if TYPE_CHECKING:
    from projects.models import Project
    from users.models import User
    from django.db.models import QuerySet


def get_request_by_pk(pk: int) -> Optional[TaskRequest]:
    """Return request by primary key."""
    return TaskRequest.objects.filter(pk=pk).first()


def get_requests_for_project(project: Project) -> QuerySet[TaskRequest]:
    """Return requests for project."""
    return TaskRequest.objects.filter(project=project).order_by("-created_at")


def get_requests_by_author(project: Project, author: User) -> QuerySet[TaskRequest]:
    """Return requests created by user within project."""
    return TaskRequest.objects.filter(project=project, author=author).order_by(
        "-created_at"
    )


def get_request_comments(req: TaskRequest) -> QuerySet[RequestComment]:
    """Return comments by request."""
    return RequestComment.objects.filter(request=req).order_by("created_at")


def get_request_status_choices() -> list[tuple[str, str]]:
    """Return available request statuses."""
    return RequestStatus.choices


def get_filtered_requests_for_project(
    project: Project, 
    user: User, 
    search_query: str = "", 
    status_filter: str = ""
) -> QuerySet[TaskRequest]:
    """
    Return requests for project filtered by search query and status.
    """

    if can_handle_requests(user, project):
        queryset = TaskRequest.objects.filter(project=project)
    else:
        queryset = TaskRequest.objects.filter(project=project, author=user)

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    if search_query:
        queryset = queryset.filter(
            Q(description__icontains=search_query) | 
            Q(author__username__icontains=search_query)
        )

    return queryset.order_by("-created_at")
