from django.contrib import admin

from common.admin import SoftDeleteAdmin

from .models import Task, TaskComment


@admin.register(Task)
class TaskAdmin(SoftDeleteAdmin):
    list_display = ('name', 'project', 'status', 'priority', 'assignments_count', 'is_deleted')
    list_filter = ('status', 'priority', 'project', 'is_deleted')
    search_fields = ('name', 'description')
    actions = ['mark_in_progress', 'mark_done']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('assignments')

    def assignments_count(self, obj):
        return obj.assignments.count()
    assignments_count.short_description = 'Исполнителей'

    def mark_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
    mark_in_progress.short_description = "Перевести в работу"

    def mark_done(self, request, queryset):
        queryset.update(status='done')
    mark_done.short_description = "Отметить выполненными"

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
