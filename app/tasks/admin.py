from django.contrib import admin
from .models import Task, TaskRequest, Comment, Notification

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'assignee', 'deadline')
    list_filter = ('status', 'priority', 'project', 'is_deleted')
    search_fields = ('title', 'description')
    actions = ['soft_delete', 'restore', 'mark_in_progress', 'mark_done']


    @admin.action(description='Удалить выбранные задачи (в корзину)')
    def soft_delete(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_deleted=True, deleted_at=timezone.now())

    @admin.action(description='Восстановить выбранные задачи')
    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)

    def mark_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
    mark_in_progress.short_description = "Перевести в работу"

    def mark_done(self, request, queryset):
        queryset.update(status='done')
    mark_done.short_description = "Отметить выполненными"

@admin.register(TaskRequest)
class TaskRequestAdmin(admin.ModelAdmin):
    list_display = ('project', 'author', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'text', 'is_read', 'created_at')