from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    username = models.CharField(
        'username',
        max_length=32,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w\-]+$',
            message='Имя пользователя может содержать только буквы, цифры, дефис и подчёркивание.'
        )],
        help_text='Только буквы, цифры, дефис и подчёркивание.',
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        max_length=128,
    )
    bio = models.TextField(blank=True, verbose_name='О себе', max_length=150)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    pending_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Неподтверждённый email',
        max_length=128,
    )

    def __str__(self):
        return self.username
        
