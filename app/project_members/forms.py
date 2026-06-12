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
        perms = kwargs.pop('perms', None)
        super().__init__(*args, **kwargs)
        
        if perms:
            self.fields['role'].choices = [
                (role_key, role_label) 
                for role_key, role_label in ProjectRole.choices 
                if perms.can_add_target_role(role_key)
            ]

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if self.perms and not self.perms.can_add_target_role(role):
            raise forms.ValidationError("У вас нет прав назначать эту роль.")
        return role
