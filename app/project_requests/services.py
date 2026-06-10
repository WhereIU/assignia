from __future__ import annotations
from typing import TYPE_CHECKING

from django.db import transaction

from core.services import create_notification

from .constants import RequestStatus
from .models import RequestMessage, TaskRequest

if TYPE_CHECKING:
    from projects.models import Project
    from users.models import User
    from project_tasks.models import Task


def create_request(
    *, project: Project, author: User, description: str
) -> TaskRequest:
    """Create new request."""
    return TaskRequest.objects.create(
        project=project,
        author=author,
        description=description,
    )


def add_message(*, req: TaskRequest, author: User, text: str) -> RequestMessage:
    """Add message to request."""
    return RequestMessage.objects.create(request=req, author=author, text=text)


def decline_request(*, req: TaskRequest) -> TaskRequest:
    """Mark request as declined and notify author."""
    req.status = RequestStatus.DECLINED
    req.save(update_fields=["status"])

    create_notification(
        recipient=req.author,
        text=f"Ваш запрос в проекте «{req.project.name}» отклонён",
        target_object=req
    )
    return req


@transaction.atomic
def convert_request_to_task(*, req: TaskRequest, actor: User) -> Task:
    """Convert request into new task and mark request as converted."""
    from project_tasks.models import Task

    task = Task.objects.create(
        project=req.project,
        name=req.description[:100],
        creator=actor,
    )
    create_notification(
        recipient=req.author,
        text=f"На основе вашего запроса в проекте «{req.project.name}» создана задача",
        target_object=req
    )
    req.status = RequestStatus.CONVERTED
    req.save(update_fields=["status"])
    return task


def update_request_status(
    *, req: TaskRequest, status: RequestStatus
) -> TaskRequest:
    """Update status of request."""
    req.status = status
    req.save(update_fields=["status"])
    return req


def delete_request(*, req: TaskRequest) -> None:
    """Permanently delete a request."""
    req.delete()
