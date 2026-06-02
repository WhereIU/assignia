from django.contrib import admin

from common.admin import SoftDeleteAdmin

from .models import Team


@admin.register(Team)
class TeamAdmin(SoftDeleteAdmin):
    list_display = ('name', 'direction', 'is_deleted')
    list_filter = ('is_deleted',)
