from django import forms
from .models import Direction


class DirectionForm(forms.ModelForm):
    class Meta:
        model = Direction
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'maxlength': '32',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание задач направления (макс. 64 символа)',
                'maxlength': '64',
            }),
        }
        labels = {
            'name': 'Название направления',
            'description': 'Описание',
        }
