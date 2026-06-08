from django import forms

from .models import ProjectMembership
from .constants import ProjectRole


class MemberRoleForm(forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-select',
            })
        }
        labels = {
            'role': 'Выберите роль',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            (choice_key, choice_value) 
            for choice_key, choice_value in ProjectRole.choices 
            if choice_key != ProjectRole.OWNER
        ]
