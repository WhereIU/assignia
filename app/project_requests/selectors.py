from __future__ import annotations
from typing import Optional, TYPE_CHECKING

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
