from __future__ import annotations
from typing import Union, TYPE_CHECKING

from django.core.paginator import Paginator

from .constants import FILTER_HEADERS

if TYPE_CHECKING:
    from django.core.paginator import Page
    from django.http import HttpRequest
    from django.db.models import QuerySet


def get_page_filters(request: HttpRequest) -> dict:
    """Extract filter values from request's GET parameters.
    """
    return {
        key: request.GET.get(key, "")
        for key in FILTER_HEADERS
    }


def get_paginated_page(queryset: QuerySet, page: Union[int, str], per_page: int = 10) -> Page:
    """Paginate queryset and return page object."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page)