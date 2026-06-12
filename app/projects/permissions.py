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
    
    @property
    def is_owner(self) -> bool:
        return self.project.owner == self.user

    @property
    def can_assign_role(self, role_to_assign: str) -> bool:
        """
        Check if user can assign role to target.
        """
        if self.is_owner:
            return role_to_assign != 'owner'
            
        if not self.membership:
            return False
            
        current_role = self.membership.role

        if current_role == 'admin':
            return role_to_assign in ['manager', 'developer', 'guest']

        if current_role == 'manager':

            return role_to_assign in ['developer', 'guest']

        return False
