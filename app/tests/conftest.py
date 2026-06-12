import pytest

from django.contrib.auth import get_user_model

from projects.models import Project
from project_members.models import ProjectMembership
from project_members.constants import ProjectRole

User = get_user_model()

@pytest.fixture
def user_factory():
    def create(username="user"):
        return User.objects.create_user(username=username, email=f"{username}@test.com")
    return create

@pytest.fixture
def project(user_factory):
    return Project.objects.create(name="Test Project", owner=user_factory(username="owner"))

@pytest.fixture
def membership_factory():
    def create(user, project, role=ProjectRole.PARTICIPANT):
        return ProjectMembership.objects.create(user=user, project=project, role=role)
    return create