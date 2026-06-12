import json
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm as DjangoUserCreationForm,
    UserChangeForm, 
    PasswordChangeForm as DjangoPasswordChangeForm,  
    AuthenticationForm
)
from django.core.cache import cache
from django.core.exceptions import ValidationError

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите username',
            'maxlength': 32,
        })
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password',
        })
    )

    error_messages = {
        "invalid_login": "Неверный логин или пароль.",
        "inactive": "Подтвердите email перед входом.",
    }

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                "Подтвердите email перед входом.",
                code="inactive",
            )


class UserCreationForm(DjangoUserCreationForm):
    email = forms.EmailField(
        max_length=128,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
            'maxlength': 128,
        })
    )

    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email'
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'Пользователь с таким именем уже существует.'
            )
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Пользователь с такой почтой уже существует.'
            )
        return email

    def clean(self):
        """Дополнительная проверка: свободны ли данные в оперативной памяти Redis."""
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")
        
        if username or email:
            for key in cache.iter_keys("temp_user:*"):
                raw_data = cache.get(key)
                if raw_data:
                    cached_user = json.loads(raw_data)
                    
                    if username and cached_user.get("username") == username:
                        self.add_error("username", "Этот логин сейчас ожидает подтверждения регистрации.")
                        
                    if email and cached_user.get("email") == email:
                        self.add_error("email", "На эту почту уже отправлено письмо, подтвердите его.")
                        
        return cleaned_data


class ProfileEditForm(UserChangeForm):
    password = None
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    bio = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'maxlength': 150,
            'placeholder': 'Расскажите о себе',
            "style": "resize:none;",
        })
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'bio',
            'avatar',
        )
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'bio': 'О себе',
            'avatar': 'Аватар',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя',
                'maxlength': 32,
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Фамилия',
                'maxlength': 32,
            }),
        }


class AccountEmailForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=128,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "email@example.com",
            "maxlength": 128,
            })
    )

    class Meta:
        model = User
        fields = ('email',)
        labels = {'email': 'Email'}

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if email == self.instance.email:
            raise forms.ValidationError(
                'Это уже ваш текущий email.'
            )
        if email == self.instance.pending_email:
            raise forms.ValidationError(
                'Этот email уже ожидает подтверждения.'
            )

        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                'Этот email уже используется.'
            )

        if User.objects.filter(pending_email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                'Этот email уже ожидает подтверждения другим пользователем.'
            )

        return email


class PasswordChangeForm(DjangoPasswordChangeForm):
    old_password_label = 'Старый пароль'
    new_password1_label = 'Новый пароль'
    new_password2_label = 'Подтверждение нового пароля'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = self.old_password_label
        self.fields['new_password1'].label = self.new_password1_label
        self.fields['new_password2'].label = self.new_password2_label
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.error_messages = {
            'password_incorrect': 'Старый пароль введён неверно. Пожалуйста, попробуйте снова.',
            'password_mismatch': 'Новые пароли не совпадают.',
            'password_too_short': 'Пароль слишком короткий.',
            'password_common': 'Пароль слишком простой.',
            'password_entirely_numeric': 'Пароль не может состоять только из цифр.',
        }
