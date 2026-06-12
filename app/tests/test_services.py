import pytest

from django.core.exceptions import ValidationError
from projects.services import send_project_invitation
from project_members.services import update_member_role, remove_member
from project_members.constants import ProjectRole

@pytest.mark.django_db
class TestProjectServices:

    def test_send_invitation_success(self, project, user_factory):
        sender = project.owner
        recipient = user_factory(username="recipient")
        
        invitation = send_project_invitation(sender=sender, recipient=recipient, project=project)
        assert invitation.recipient == recipient
        assert invitation.status == "pending"

    def test_send_invitation_self_fail(self, project):
        with pytest.raises(ValidationError, match="Нельзя пригласить самого себя"):
            send_project_invitation(sender=project.owner, recipient=project.owner, project=project)

    def test_update_member_role(self, project, user_factory, membership_factory):
        user = user_factory(username="test")
        membership = membership_factory(user=user, project=project)
        
        update_member_role(target_membership=membership, new_role=ProjectRole.ADMIN)
        membership.refresh_from_db()
        assert membership.role == ProjectRole.ADMIN

    def test_remove_member(self, project, user_factory, membership_factory):
        user = user_factory(username="to_delete")
        membership = membership_factory(user=user, project=project)
        
        username = remove_member(target_membership=membership)
        assert username == "to_delete"
        assert not membership.pk
