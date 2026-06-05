from __future__ import annotations
from typing import TYPE_CHECKING

from django.contrib import messages


if TYPE_CHECKING:
    from django.http import HttpRequest


def message_success(request: HttpRequest, message: str):
    return messages.success(request=request, message=message)


def message_error(request: HttpRequest, message: str):
    return messages.error(request=request, message=message)