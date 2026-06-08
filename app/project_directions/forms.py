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
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание задач направления',
            }),
        }
        labels = {
            'name': 'Название направления',
            'description': 'Описание',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Название направления обязательно")
        return name
