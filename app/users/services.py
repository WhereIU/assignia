from __future__ import annotations
import uuid
import json
from typing import Any, Dict, Optional, TYPE_CHECKING

from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.hashers import make_password

if TYPE_CHECKING:
    from .models import User

EMAIL_CONFIRMATION_TIMEOUT = 60 * 60
REGISTRATION_TIMEOUT = 30 * 60


def save_temp_user_to_cache(form_data: dict) -> str:
    """Hashes the password, stores the form data in Redis, and generates a token."""
    token = str(uuid.uuid4())
    
    temp_user_data = {
        "username": form_data.get("username"),
        "email": form_data.get("email"),
        "first_name": form_data.get("first_name", ""),
        "last_name": form_data.get("last_name", ""),
        "password": make_password(form_data.get("password1")),
    }
    
    cache.set(f"temp_user:{token}", json.dumps(temp_user_data), timeout=REGISTRATION_TIMEOUT)
    return token


def send_registration_confirmation(form_data: dict) -> str:
    """
    Saves data to the cache,
    builds a URL, and sends an email. Returns a token.
    """
    token = save_temp_user_to_cache(form_data)
    url = settings.BASE_URL + reverse("users:confirm_email", kwargs={"token": token})
    
    context = {
        "username": form_data.get("username"),
        "url": url,
    }
    
    subject = render_to_string("users/emails/registration_subject.txt", context).strip()
    message = render_to_string("users/emails/registration_body.txt", context)
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[form_data.get("email")],
            fail_silently=False,
        )
    except Exception as exc:
        cache.delete(f"temp_user:{token}")
        raise RuntimeError("Не удалось отправить письмо подтверждения.") from exc
        
    return token


def create_user_from_cache(token: str) -> Optional[User]:
    """Extracts data from Redis, creates an active user in the database and deletes the token."""
    raw_data = cache.get(f"temp_user:{token}")
    if not raw_data:
        return None
        
    user_data = json.loads(raw_data)
    from users.models import User
    
    if User.objects.filter(username=user_data["username"]).exists() or \
       User.objects.filter(email=user_data["email"]).exists():
        return None

    user = User.objects.create(
        username=user_data["username"],
        email=user_data["email"],
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name", ""),
        password=user_data["password"]
    )
    
    cache.delete(f"temp_user:{token}")
    return user


def _generate_email_confirmation_token(user: User, new_email: Optional[str] = None) -> str:
    """Generate and store unique token for email confirmation."""
    old_token = cache.get(f"user_email_confirmation:{user.pk}")
    if old_token:
        cache.delete(f"email_confirmation:{old_token}")

    token = str(uuid.uuid4())
    cache.set(
        f"email_confirmation:{token}",
        {
            "user_id": user.id,
            "new_email": new_email,
        },
        timeout=EMAIL_CONFIRMATION_TIMEOUT,
    )
    return token


def send_email_confirmation(user: User, new_email: Optional[str] = None) -> None:
    """Send confirmation email."""
    token = _generate_email_confirmation_token(user, new_email)
    url = settings.BASE_URL + reverse("users:confirm_email", kwargs={"token": token})

    context = {"url": url}
    subject = render_to_string("users/emails/change_email_subject.txt", context).strip()
    message = render_to_string("users/emails/change_email_body.txt", context)

    recipient = new_email or user.email
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as exc:
        raise RuntimeError("Не удалось отправить письмо.") from exc

    user.pending_email = new_email
    user.save(update_fields=["pending_email"])


def confirm_email_token(token: str) -> Optional[User]:
    """Validate token and activate."""
    data: Optional[Dict[str, Any]] = cache.get(f"email_confirmation:{token}")
    if not data:
        return None

    from users.models import User
    user = User.objects.filter(id=data["user_id"]).first()
    if not user:
        return None

    if data["new_email"]:
        user.email = data["new_email"]
        user.pending_email = None
        user.save(update_fields=["email", "pending_email"])

    user.is_active = True
    user.save(update_fields=["is_active"])
    cache.delete(f"email_confirmation:{token}")
    return user


def cancel_pending_email(user: User) -> None:
    """Cancel pending email change."""
    user.pending_email = None
    user.save(update_fields=["pending_email"])


def change_user_email(user: User, new_email: str) -> None:
    """Check for existing pending email, send confirmation and mark pending."""
    if user.pending_email:
        raise ValueError("У вас уже есть неподтверждённый email.")
    try:
        send_email_confirmation(user, new_email)
    except Exception as exc:
        raise RuntimeError("Не удалось отправить письмо.") from exc
    user.refresh_from_db()


def delete_user_avatar(user: User) -> bool:
    """Delete user avatar and clear avatar media."""
    if user.avatar:
        user.avatar.delete(save=True)
        return True
    return False
