from __future__ import annotations
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

from project_members.selectors import get_project_ids_for_user
from project_members.services import create_membership
from .models import Invitation, Project
from .selectors import get_pending_status_value, get_default_invitation_role

if TYPE_CHECKING:
    from .forms import ProjectCreateForm
    from users.models import User


def create_project(*, form: ProjectCreateForm, user: User) -> Project:
    """Save new project from form."""
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
    *, 
    sender: User, 
    recipient: User, 
    project: Project, 
    role: str | None = None 
) -> Invitation:
    """Send invitation after validation; raises ValidationError on failure."""
    if recipient == sender:
        raise ValidationError("Нельзя пригласить самого себя")
        
    user_project_ids = get_project_ids_for_user(recipient)
    if project.pk in user_project_ids:
        raise ValidationError("Пользователь уже участник проекта")
        
    pending_status = get_pending_status_value()
    if Invitation.objects.filter(
        recipient=recipient, project=project, status=pending_status
    ).exists():
        raise ValidationError("Приглашение уже существует")

    if role is None:
        role = get_default_invitation_role()

    return Invitation.objects.create(
        sender=sender, recipient=recipient, project=project, role=role
    )


def cancel_invitation(*, invitation: Invitation) -> None:
    """Cancel pending invitation."""
    invitation.status = "cancelled"
    invitation.save(update_fields=["status"])


def accept_invitation(*, invitation: Invitation, user: User) -> None:
    """Accept invitation, create membership if not member yet, mark accepted."""
    user_project_ids = get_project_ids_for_user(user)
    if invitation.project.pk not in user_project_ids:
        create_membership(
            user=user, 
            project=invitation.project, 
            role=invitation.role
        )
    invitation.status = "accepted"
    invitation.save(update_fields=["status"])


def decline_invitation(*, invitation: Invitation) -> None:
    """Decline invitation."""
    invitation.status = "declined"
    invitation.save(update_fields=["status"])
