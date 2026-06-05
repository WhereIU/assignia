from __future__ import annotations
from typing import TYPE_CHECKING

from django.urls import reverse
from django.db import transaction

from core.services import create_notification

from .constants import RequestStatus
from .models import RequestComment, TaskRequest

if TYPE_CHECKING:
    from projects.models import Project
    from users.models import User
    from project_tasks.models import Task


def create_request(
    *, project: Project, author: User, description: str
) -> TaskRequest:
    """Create a new request."""
    return TaskRequest.objects.create(
        project=project,
        author=author,
        description=description,
    )


def add_comment(*, req: TaskRequest, author: User, text: str) -> RequestComment:
    """Add a comment to a request."""
    return RequestComment.objects.create(request=req, author=author, text=text)


def decline_request(*, req: TaskRequest) -> TaskRequest:
    """Mark a request as declined and notify the author."""
    req.status = RequestStatus.DECLINED
    req.save(update_fields=["status"])

    create_notification(
        recipient=req.author,
        text=f"Ваш запрос в проекте «{req.project.name}» отклонён",
        url=reverse('project_requests:request_detail', kwargs={'request_pk': req.pk})
    )
    return req


@transaction.atomic
def convert_request_to_task(*, req: TaskRequest, actor: User) -> Task:
    """
    Convert a request into a new task and mark the request as converted.
    TODO: Replace direct Task creation with tasks.services call once available.
    """
    from project_tasks.models import Task  # local import to avoid circular deps

    task = Task.objects.create(
        project=req.project,
        name=req.description[:100],
        creator=actor,
    )
    req.status = RequestStatus.CONVERTED
    req.save(update_fields=["status"])
    return task


def update_request_status(
    *, req: TaskRequest, status: RequestStatus
) -> TaskRequest:
    """Update the status of a request."""
    req.status = status
    req.save(update_fields=["status"])
    return req


def delete_request(*, req: TaskRequest) -> None:
    """Permanently delete a request."""
    req.delete()