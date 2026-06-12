from project_members.permissions import ProjectBasePermissions
from project_members.constants import ProjectRole

class ProjectDirectionsPermissions(ProjectBasePermissions):
    """Class of direction permissions."""

    @property
    def can_view_directions(self) -> bool:
        """Check if the user is allowed to view directions.."""
        if self.project.is_public:
            return True
        return self.is_member

    @property
    def can_manage_directions(self) -> bool:
        """Who can manage directions."""
        if not self.is_member:
            return False
        return self.member_role in (ProjectRole.ADMIN, ProjectRole.OWNER)
