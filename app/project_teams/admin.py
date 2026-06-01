from django.contrib import admin

from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'direction', 'is_deleted')
    list_filter = ('is_deleted',)
    actions = ['soft_delete', 'restore']

    @admin.action(description='Удалить команды (в корзину)')
    def soft_delete(self, request, queryset):
        queryset.update(is_deleted=True)

    @admin.action(description='Восстановить команды')
    def restore(self, request, queryset):
        queryset.update(is_deleted=False)
