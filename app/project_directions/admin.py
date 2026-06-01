from django.contrib import admin

from .models import Direction


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'is_deleted')
    list_filter = ('is_deleted',)
    actions = ['soft_delete', 'restore']

    @admin.action(description='Удалить направления (в корзину)')
    def soft_delete(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_deleted=True, deleted_at=timezone.now())

    @admin.action(description='Восстановить направления')
    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)


