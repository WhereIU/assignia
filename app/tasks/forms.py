from django import forms

from divisions.models import Direction, Team

from .models import Task


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'directions', 'teams', 'priority', 'risk_chance', 'risk_impact']
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'directions': 'Направления',
            'teams': 'Команды',
            'priority': 'Приоритет (1-5)',
            'risk_chance': 'Шанс риска (1-5)',
            'risk_impact': 'Последствия риска (1-5)',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'directions': forms.CheckboxSelectMultiple,
            'teams': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if self.project:
            self.fields['directions'].queryset = Direction.objects.filter(project=self.project, is_deleted=False)
            self.fields['teams'].queryset = Team.objects.filter(direction__project=self.project, is_deleted=False)
