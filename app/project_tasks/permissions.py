from project_members.permissions import ProjectBasePermissions
from project_members.constants import ProjectRole


class ProjectTasksPermissions(ProjectBasePermissions):
    """Permissions class for managing project tasks."""

    @property
    def can_view_tasks(self) -> bool:
        """Check if the user is allowed to view the requests."""
        if self.project.is_public:
            return True
        return self.is_member

    @property
    def can_create_tasks(self) -> bool:
        """Can create task."""
        return self.is_member

    @property
    def can_manage_tasks(self) -> bool:
        """
        Can manage details of task.
        """
        if not self.is_member:
            return False
        return self.role_weight >= self._get_role_weight(ProjectRole.MANAGER)
