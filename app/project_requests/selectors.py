from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from django.db.models import Q
from django.urls import reverse

from common.selectors import get_paginated_page
from project_members.permissions import can_handle_requests
from project_requests.constants import RequestStatus

from .models import RequestMessage, TaskRequest

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


def get_request_messages(req: TaskRequest) -> QuerySet[RequestMessage]:
    """Return messages by request."""
    return RequestMessage.objects.filter(request=req).order_by("created_at")


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


def get_messages_context(req, page_number=1) -> dict:
    messages_queryset = get_request_messages(req=req).order_by("-created_at")
    
    page_obj = get_paginated_page(queryset=messages_queryset, page=page_number, per_page=10)
    
    fixed_path = reverse("project_requests:request_detail", kwargs={"request_pk": req.pk})
    
    return {
        "req": req,
        "messages_list": page_obj.object_list,
        "page_obj": page_obj,
        "fixed_path": fixed_path,
    }
