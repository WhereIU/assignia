from project_members.permissions import ProjectBasePermissions
from project_members.constants import ProjectRole


class ProjectPermissions(ProjectBasePermissions):
    """Permissions class for project."""

    @property
    def can_view_project(self) -> bool:
        """Can view project."""
        if self.project.is_public:
            return True
        return self.is_member

    @property
    def can_manage_invitations(self) -> bool:
        """Can send, cancel or view invitations."""
        if not self.is_member:
            return False
        return self.role_weight >= self._get_role_weight(ProjectRole.MANAGER)

    @property
    def can_manage_settings(self) -> bool:
        """Can update project settings."""
        if not self.is_member:
            return False
        return self.role_weight >= self._get_role_weight(ProjectRole.ADMIN)

    @property
    def can_delete_project(self) -> bool:
        """Can delete project."""
        return self.is_owner
