import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from projects.models import Project
from project_members.models import ProjectMembership
from users.models import User

@pytest.mark.django_db
class TestModels:

    def test_project_str(self, project):
        """Checking __str__ in the project."""
        assert str(project) == project.name

    def test_project_slug_generation(self, user_factory):
        """Check that the slug is generated automatically."""
        user = user_factory()
        project = Project.objects.create(name="testovyy-proekt", owner=user)
        assert project.slug == "testovyy-proekt"

    def test_unique_owner_slug(self, user_factory):
        """Checking the unique_together constraint on owner and slug."""
        user = user_factory()
        Project.objects.create(name="Project A", owner=user, slug="same-slug")
        
        with pytest.raises(IntegrityError):
            Project.objects.create(name="Project B", owner=user, slug="same-slug")

    def test_membership_unique_together(self, project, user_factory):
        """Check that one user cannot be a participant in the same project twice."""
        user = user_factory()
        ProjectMembership.objects.create(user=user, project=project)
        
        with pytest.raises(IntegrityError):
            ProjectMembership.objects.create(user=user, project=project)

    def test_user_email_constraint(self):
        """We check that the email cannot be empty."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(username="testuser", email="")
