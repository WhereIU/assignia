from typing import Optional

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from projects.models import Project

from .models import ProjectMembership
from .constants import ProjectRole, ROLE_WEIGHTS


class ProjectBasePermissions:
    """Base permissions class for project memberships."""
    
    def __init__(self, user: AbstractBaseUser | AnonymousUser, project: Project):
        self.user = user
        self.project = project
        self._membership: Optional[ProjectMembership] = None
        self._membership_fetched = False

    @property
    def membership(self) -> Optional[ProjectMembership]:
        """Return cached project membership for the current user."""
        if not self._membership_fetched:
            if self.user and self.user.is_authenticated:
                self._membership = ProjectMembership.objects.filter(
                    project=self.project, user=self.user
                ).select_related("user").first()
            self._membership_fetched = True
        return self._membership

    @property
    def role(self) -> Optional[str]:
        """Return the role name of the current user."""
        return self.membership.role if self.membership else None

    @property
    def role_weight(self) -> int:
        """Return numerical hierarchy weight of the current user role."""
        if self.user and self.user.is_superuser:
            return 100
        return self._get_role_weight(self.role)

    @property
    def is_member(self) -> bool:
        """Check if the current user is a member of the project."""
        if not self.user or not self.user.is_authenticated:
            return False
        return self.membership is not None or self.user.is_superuser

    def _get_role_weight(self, role: Optional[str]) -> int:
        """Return hierarchy weight for a role string."""
        return ROLE_WEIGHTS.get(role, 0)


class ProjectMembersPermissions(ProjectBasePermissions):
    """Permissions for managing project members and their roles."""

    @property
    def can_view_member_tab(self) -> bool:
        """Check if user can view the project members tab."""
        if self.project.is_public:
            return True
        return self.is_member

    @property
    def can_manage_members(self) -> bool:
        """Check if user has minimal privileges to access management features."""
        return self.role_weight >= self._get_role_weight(ProjectRole.HR_ANALYST)

    def can_add_target_role(self, target_role: str) -> bool:
        """Check if user can assign a specific role to a new or existing member."""
        if target_role == ProjectRole.OWNER:
                return False

        if not self.can_manage_members:
            return False
            
        return self.role_weight > self._get_role_weight(target_role)

    def can_edit_member(self, target_membership: Optional[ProjectMembership]) -> bool:
        """Check if user can modify or remove a specific member."""
        if not self.user or not self.user.is_authenticated or not target_membership:
            return False
        if self.user.is_superuser or self.project.owner == self.user:
            return True
        if target_membership.user == self.user:
            return False
        if not self.can_manage_members:
            return False
            
        return self.role_weight > self._get_role_weight(target_membership.role)
