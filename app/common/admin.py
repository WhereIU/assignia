from django.contrib import admin
from django.utils import timezone


class SoftDeleteAdmin(admin.ModelAdmin):
    @admin.action(
        description="Переместить в корзину"
    )
    def soft_delete(
        self,
        request,
        queryset,
    ):
        queryset.update(
            is_deleted=True,
            deleted_at=timezone.now(),
        )

    @admin.action(
        description="Восстановить"
    )
    def restore(
        self,
        request,
        queryset,
    ):
        queryset.update(
            is_deleted=False,
            deleted_at=None,
        )
