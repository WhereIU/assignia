from django.conf import settings
from django.db import models

from django.db import models
from django.conf import settings
from django.utils.text import slugify

from django.db import models
from django.conf import settings

class Project(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    is_public = models.BooleanField(default=False)
    options = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'slug'], name='unique_owner_slug')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Direction(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='directions')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.project.name})"

class Team(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=200)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ProjectMembership', related_name='teams')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.project.name})"

class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('tech_support', 'Техподдержка'),
        ('hr_analyst', 'Кадровый аналитик'),
        ('participant', 'Участник'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} в {self.project.name} как {self.get_role_display()}"
