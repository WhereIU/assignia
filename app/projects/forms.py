from django import forms
from django.utils.text import slugify

from .models import Project


class ProjectCreateForm(forms.ModelForm):
    slug = forms.CharField(
        required=False,
        label='URL проекта',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'my-new-project',
            'maxlength': 50,
            'id': 'id_slug',
        }),
        help_text='Оставьте пустым для автоматической генерации из названия.',
    )

    class Meta:
        model = Project
        fields = ['name', 'slug', 'description', 'is_public']
        labels = {
            'name': 'Название проекта',
            'description': 'Описание',
            'is_public': 'Публичный проект',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Мой новый проект',
                'maxlength': 50,
                'id': 'id_name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите, чем будет заниматься проект...',
                'maxlength': 500,
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        name = self.cleaned_data.get('name', '')
        owner = self.initial.get('owner')
        if not slug:
            slug = slugify(name)
        else:
            slug = slugify(slug)

        if not slug:
            raise forms.ValidationError('Не удалось создать путь. Укажите название на английском или задайте путь вручную.')

        if owner and Project.objects.filter(owner=owner, slug=slug).exists():
            raise forms.ValidationError('У вас уже есть проект с таким путём. Измените название или задайте другой путь.')

        return slug

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Название не может быть пустым.')
        return name
