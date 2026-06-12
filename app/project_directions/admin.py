from django.contrib import admin

from common.admin import SoftDeleteAdmin

from .models import Direction


class DirectionAdmin(SoftDeleteAdmin):
    list_display = (
        "name",
        "project",
        "is_deleted",
    )

    actions = [
        "soft_delete",
        "restore",
    ]
