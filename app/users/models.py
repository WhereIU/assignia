from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    username = models.CharField(
        'username',
        max_length=150,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w\-]+$',
            message='Имя пользователя может содержать только буквы, цифры, дефис и подчёркивание.'
        )],
        help_text='Только буквы, цифры, дефис и подчёркивание.',
    )
    bio = models.TextField(blank=True, verbose_name='О себе')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.username