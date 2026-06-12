from django.contrib import admin

from .models import TaskRequest


@admin.register(TaskRequest)
class TaskRequestAdmin(admin.ModelAdmin):
    list_display = ('project', 'author', 'status', 'created_at')
    list_filter = ('status',)
