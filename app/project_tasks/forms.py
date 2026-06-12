from django import forms
from .models import Task

class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description', 'priority', 'risk_chance', 'risk_impact', 'deadline']
        labels = {
            'name': 'Название задачи',
            'description': 'Описание',
            'priority': 'Приоритет',
            'risk_chance': 'Шанс риска',
            'risk_impact': 'Последствия риска',
            'deadline': 'Дедлайн',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Кратко опишите задачу',
                'maxlength': 64,
                'id': 'id_task_name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Подробное описание задачи',
                'maxlength': 1000,
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'risk_chance': forms.Select(attrs={'class': 'form-select'}),
            'risk_impact': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local',
                    'max': '3000-12-31T23:59',
                }
            ),
        }
