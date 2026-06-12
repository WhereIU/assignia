from project_members.permissions import ProjectMembersPermissions
from project_members.constants import ProjectRole


class ProjectPermissions(ProjectMembersPermissions):
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
        return self.role_weight >= self._get_role_weight(ProjectRole.HR_ANALYST)

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
    
    @property
    def is_owner(self) -> bool:
        return self.project.owner == self.user

    @property
    def can_assign_role(self, target_role: str) -> bool:
        """
        Check if user can assign a specific role to a new or existing member.
        """
        if target_role == ProjectRole.OWNER:
            return False

        if self.user.is_superuser:
            return True

        if self.project.owner == self.user:
            return target_role != ProjectRole.OWNER

        if self.can_manage_members:
            current_weight = self.role_weight
            target_weight = self._get_role_weight(target_role)
            
            return current_weight > target_weight
            
        return False
