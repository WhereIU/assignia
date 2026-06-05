from __future__ import annotations
from typing import TYPE_CHECKING

from django.shortcuts import get_object_or_404

from .models import RequestComment, TaskRequest

if TYPE_CHECKING:
    from projects.models import Project
    from users.models import User
    from django.db.models import QuerySet


def get_request_by_pk(pk: int) -> TaskRequest:
    """Return request by primary key, or 404."""
    return get_object_or_404(TaskRequest, pk=pk)


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
