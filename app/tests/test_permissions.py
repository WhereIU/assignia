import pytest

from project_members.constants import ProjectRole
from projects.permissions import ProjectPermissions

@pytest.mark.django_db
class TestProjectPermissions:
    
    def test_owner_permissions(self, project):
        perms = ProjectPermissions(project.owner, project)
        assert perms.can_delete_project is True
        assert perms.can_manage_settings is True
        assert perms.can_manage_invitations is True

    def test_participant_permissions(self, project, user_factory, membership_factory):
        participant = user_factory(username="participant")
        membership_factory(user=participant, project=project, role=ProjectRole.PARTICIPANT)
        
        perms = ProjectPermissions(participant, project)
        assert perms.can_manage_settings is False
        assert perms.can_delete_project is False

    def test_role_hierarchy_management(self, project, user_factory, membership_factory):
        manager = user_factory(username="manager")
        member = user_factory(username="member")
        membership_factory(user=manager, project=project, role=ProjectRole.MANAGER)
        member_ship = membership_factory(user=member, project=project, role=ProjectRole.PARTICIPANT)
        
        perms = ProjectPermissions(manager, project)
        assert perms.can_edit_member(member_ship) is True
