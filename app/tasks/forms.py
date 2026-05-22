from django import forms

from projects.models import Direction

from .models import Task


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'direction', 'priority', 'risk_chance', 'risk_impact']
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'direction': 'Направление',
            'priority': 'Приоритет (1-5)',
            'risk_chance': 'Шанс риска (1-5)',
            'risk_impact': 'Последствия риска (1-5)',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        super().__init__(*args, **kwargs)
        self.fields['direction'].queryset = Direction.objects.filter(project=self.project, is_deleted=False)
        self.fields['direction'].required = False