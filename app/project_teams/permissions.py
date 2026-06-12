from project_members.permissions import ProjectBasePermissions
from project_members.constants import ProjectRole


class ProjectTeamsPermissions(ProjectBasePermissions):
    """Class of team permissions."""

    @property
    def can_view_teams(self) -> bool:
        """Check if the user is allowed to view teams."""
        if self.project.is_public:
            return True
        return self.is_member

    @property
    def can_manage_teams(self) -> bool:
        """Check if the user is allowed to create/edit/delete teams and change rosters."""
        if not self.is_member:
            return False
        return self.role in (ProjectRole.ADMIN, ProjectRole.OWNER)
