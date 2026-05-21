from django import forms
from .models import Project
from django.utils.text import slugify

class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'is_public']
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'is_public': 'Публичный проект',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        slug = slugify(name)
        if Project.objects.filter(owner=self.initial.get('owner'), slug=slug).exists():
            raise forms.ValidationError('У вас уже есть проект с таким названием.')
        return name