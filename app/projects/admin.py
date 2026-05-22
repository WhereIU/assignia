from django.contrib import admin
from .models import Project, Direction, Team, ProjectMembership


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'created_at')
    list_filter = ('is_public', )
    search_fields = ('name', 'description')

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'is_deleted')
    list_filter = ('is_deleted', )
    actions = ['soft_delete', 'restore']


    @admin.action(description='Удалить направления (в корзину)')
    def soft_delete(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_deleted=True, deleted_at=timezone.now())

    @admin.action(description='Восстановить направления')
    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'is_deleted')
    list_filter = ('is_deleted',)
    actions = ['soft_delete', 'restore']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_deleted=False)

    @admin.action(description='Удалить команды (в корзину)')
    def soft_delete(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_deleted=True, deleted_at=timezone.now())

    @admin.action(description='Восстановить команды')
    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'team')
    list_filter = ('role',)
