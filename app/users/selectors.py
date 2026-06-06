from __future__ import annotations
from typing import Optional

from .models import User


def get_user_by_username(username: str) -> Optional[User]:
    """Return user by username."""
    return User.objects.filter(username=username).first()