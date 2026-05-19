import pytest
from users.models import User
from projects.models import Project, ProjectMembership
from tasks.models import Task, TaskRequest, Comment, Notification

@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(username='test', password='12345')
    assert user.username == 'test'
    assert user.check_password('12345')

@pytest.mark.django_db
def test_project_creation():
    owner = User.objects.create_user(username='owner', password='pass')
    project = Project.objects.create(name='Тестовый', owner=owner, is_public=True)
    assert project.name == 'Тестовый'
    assert project.owner == owner

@pytest.mark.django_db
def test_membership_role():
    user = User.objects.create_user(username='member', password='pass')
    owner = User.objects.create_user(username='creator', password='pass')
    project = Project.objects.create(name='Роли', owner=owner)
    membership = ProjectMembership.objects.create(user=user, project=project, role='participant')
    assert membership.role == 'participant'

@pytest.mark.django_db
def test_task_creation():
    owner = User.objects.create_user(username='tasker', password='pass')
    project = Project.objects.create(name='Задачи', owner=owner)
    task = Task.objects.create(project=project, title='Тестовая задача', creator=owner, priority=3)
    assert task.status == 'new'
    assert task.priority == 3

@pytest.mark.django_db
def test_task_request_creation():
    user = User.objects.create_user(username='req_user', password='pass')
    owner = User.objects.create_user(username='proj_owner', password='pass')
    project = Project.objects.create(name='Проект с запросами', owner=owner)
    req = TaskRequest.objects.create(project=project, author=user, description='Нужна фича')
    assert req.status == 'pending'

@pytest.mark.django_db
def test_comment_and_notification(settings):
    creator = User.objects.create_user(username='creator', password='pass')
    assignee = User.objects.create_user(username='assignee', password='pass')
    project = Project.objects.create(name='Комменты', owner=creator)
    task = Task.objects.create(project=project, title='Обсуждаемая', creator=creator, assignee=assignee)
    comment = Comment.objects.create(task=task, author=assignee, text='Готово')
    assert comment.task == task
    assert Notification.objects.filter(recipient=creator, is_read=False).exists()