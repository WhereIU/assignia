from __future__ import annotations
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

from project_members.permissions import is_project_member
from project_members.services import create_membership
from .constants import InvitationStatus
from .models import Invitation, Project

if TYPE_CHECKING:
    from .forms import ProjectCreateForm
    from users.models import User


def create_project(*, form: ProjectCreateForm, user: User) -> Project:
    """Save a new project from form. The owner is the given user."""
    project = form.save(commit=False)
    project.owner = user
    project.save()
    return project


def update_project(
    *, project: Project, name: str, description: str, is_public: bool
) -> Project:
    """Update project fields and save."""
    project.name = name
    project.description = description
    project.is_public = is_public
    project.save()
    return project


def send_project_invitation(
    *, sender: User, recipient: User, project: Project
) -> Invitation:
    """Send an invitation after validation; raises ValidationError on failure."""
    if recipient == sender:
        raise ValidationError("Нельзя пригласить самого себя")
    if is_project_member(recipient, project):
        raise ValidationError("Пользователь уже участник проекта")
    if Invitation.objects.filter(
        recipient=recipient, project=project, status=InvitationStatus.PENDING
    ).exists():
        raise ValidationError("Приглашение уже существует")
    return Invitation.objects.create(
        sender=sender, recipient=recipient, project=project
    )


def cancel_invitation(*, invitation: Invitation) -> None:
    """Cancel a pending invitation."""
    invitation.status = InvitationStatus.CANCELLED
    invitation.save(update_fields=["status"])


def accept_invitation(*, invitation: Invitation, user: User) -> None:
    """Accept an invitation: create membership if not already member, mark accepted."""
    if not is_project_member(user, invitation.project):
        create_membership(user=user, project=invitation.project)
    invitation.status = InvitationStatus.ACCEPTED
    invitation.save(update_fields=["status"])


def decline_invitation(*, invitation: Invitation) -> None:
    """Decline an invitation."""
    invitation.status = InvitationStatus.DECLINED
    invitation.save(update_fields=["status"])