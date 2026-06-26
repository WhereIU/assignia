from __future__ import annotations
from typing import Optional, TYPE_CHECKING, List, Dict

from django.db.models import Q
from django.urls import reverse

from common.selectors import get_paginated_page
from project_requests.constants import RequestStatus
from .models import RequestMessage, TaskRequest

if TYPE_CHECKING:
    from projects.models import Project
    from users.models import User
    from django.db.models import QuerySet
    from .permissions import ProjectRequestsPermissions


def get_request_by_pk(pk: int) -> Optional[TaskRequest]:
    """Return request by primary key."""
    return TaskRequest.objects.filter(pk=pk).select_related("project", "author").first()


def get_request_messages(req: TaskRequest) -> QuerySet[RequestMessage]:
    """Return messages by request."""
    return RequestMessage.objects.filter(request=req)


def get_request_status_choices() -> List[Dict[str, str]]:
    """
    Return available request statuses
    """
    return [
        {"value": value, "label": label}
        for value, label in RequestStatus.choices
    ]


def get_available_actions_for_request(
    req: TaskRequest, 
    user: User, 
    perms: ProjectRequestsPermissions
) -> Dict[str, bool]:
    """
    Return a map of authorized execution flags.
    """
    is_author = req.author == user
    is_pending = req.status == RequestStatus.PENDING

    return {
        "can_convert": perms.can_handle_requests and is_pending,
        "can_decline": perms.can_handle_requests and is_pending,
        "can_delete": is_author and is_pending,
    }


def get_filtered_requests_for_project(
    *,
    project: Project, 
    user: User, 
    perms: ProjectRequestsPermissions,
    search_query: str = "", 
    status_filter: str = ""
) -> QuerySet[TaskRequest]:
    """
    Return filtere requests for project.
    """
    if perms.can_handle_requests:
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

    return queryset.select_related("author").order_by("-created_at")


def get_messages_context(req: TaskRequest, page_number: int = 1) -> dict:
    """Return context for request messages chat."""
    messages_queryset = get_request_messages(req=req).order_by("-created_at")
    
    page_obj = get_paginated_page(queryset=messages_queryset, page=page_number, per_page=10)
    fixed_path = reverse("project_requests:request_detail", kwargs={"request_pk": req.pk})
    
    return {
        "req": req,
        "messages_list": page_obj.object_list,
        "page_obj": page_obj,
        "fixed_path": fixed_path,
    }


def is_request_pending(req: TaskRequest) -> bool:
    """Return True if the request is still pending."""
    return req.status == RequestStatus.PENDING
