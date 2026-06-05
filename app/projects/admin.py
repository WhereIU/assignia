from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'created_at')
    list_filter = ('is_public', )
    search_fields = ('name', 'description')
