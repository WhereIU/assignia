from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import User
from .forms import UserCreationForm

class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email обязателен.')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = AdminUserChangeForm
    add_form = UserCreationForm

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('bio', 'avatar', 'pending_email')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
