from django import forms

from .models import TaskRequest


class TaskRequestForm(forms.ModelForm):
    class Meta:
        model = TaskRequest
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Подробно опишите ваш запрос...',
                'style': 'resize: none;'
            }),
        }
        labels = {
            'description': 'Описание запроса',
        }

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            raise forms.ValidationError("Описание запроса не может быть пустым.")
        return description
