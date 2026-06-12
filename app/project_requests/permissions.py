from project_members.permissions import ProjectBasePermissions
from project_members.constants import ProjectRole

class ProjectRequestsPermissions(ProjectBasePermissions):
    """Permissions class for managing tech support and task requests."""

    @property
    def can_view_requests(self) -> bool:
        """Check if the user is allowed to view the requests."""
        if self.project.is_public:
            return True
        return self.is_member

    @property
    def can_create_requests(self) -> bool:
        """Can create a request."""
        return self.user and self.user.is_authenticated

    @property
    def can_handle_requests(self) -> bool:
        """Check if user has privileges to manage requests."""
        if not self.is_member:
            return False
        return self.role_weight >= self._get_role_weight(ProjectRole.TECH_SUPPORT)
