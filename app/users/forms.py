from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm as DjangoPasswordChangeForm

from .models import User


class UserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

class ProfileEditForm(UserChangeForm):
    password = None
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'bio', 'avatar')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'bio': 'О себе',
            'avatar': 'Аватар',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Расскажите о себе'}),
        }
    
class AccountEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)
        labels = {'email': 'Email'}
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Этот email уже используется.')
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