from django.shortcuts import get_object_or_404
from .models import User


def get_user_by_username(username: str) -> User:
    """Return user by username, or raise Http404."""
    return get_object_or_404(User, username=username)