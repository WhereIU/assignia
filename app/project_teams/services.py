from users.models import User
from project_members.permissions import is_project_member
from .models import Team


def create_team(*, direction, name: str) -> Team:
    """Create new team in direction."""
    return Team.objects.create(direction=direction, name=name)


def update_team(*, team: Team, name: str) -> Team:
    """Update team's name."""
    team.name = name
    team.save(update_fields=["name"])
    return team


def soft_delete_team(*, team: Team) -> Team:
    """Soft-delete team."""
    team.is_deleted = True
    team.save(update_fields=["is_deleted"])
    return team


def hard_delete_team(*, team: Team) -> None:
    """Permanently delete team."""
    team.delete()


def restore_team(*, team: Team) -> Team:
    """Restore soft-deleted team."""
    team.is_deleted = False
    team.save(update_fields=["is_deleted"])
    return team


def add_member_to_team(*, team: Team, user: User) -> None:
    """Add user to team."""
    if not is_project_member(user, team.direction.project):
        raise ValueError("Пользователь не участник проекта")
    team.members.add(user)


def remove_member_from_team(*, team: Team, user: User) -> None:
    """Remove user from team."""
    team.members.remove(user)