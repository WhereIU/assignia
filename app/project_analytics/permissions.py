from project_members.permissions import ProjectBasePermissions


class ProjectAnalyticsPermissions(ProjectBasePermissions):
    """Class of anayltics perimisisons."""

    @property
    def can_view_analytics(self) -> bool:
        """
        Check if the user is allowed to view analytics data.
        """
        if self.project.is_public:
            return True
        return self.is_member
    