from django.contrib import admin

from .models import ProjectMembership


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'team')
    list_filter = ('role',)
