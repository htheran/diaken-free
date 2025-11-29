from django import forms
from .models import Playbook
import os
import yaml


class PlaybookForm(forms.ModelForm):
    """Form for uploading playbook files"""
    class Meta:
        model = Playbook
        fields = ['name', 'description', 'playbook_type', 'os_family', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Playbook name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optional)'}),
            'playbook_type': forms.Select(attrs={'class': 'form-control'}),
            'os_family': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.yml,.yaml'}),
        }
        labels = {
            'name': 'Playbook Name',
            'description': 'Description',
            'playbook_type': 'Type',
            'os_family': 'OS Family',
            'file': 'Playbook File (.yml or .yaml)',
        }
        help_texts = {
            'playbook_type': 'Select "Host" for playbooks that run on individual hosts, or "Group" for playbooks that run on groups of hosts.',
            'os_family': 'Select the operating system family this playbook is designed for.',
        }


class PlaybookContentForm(forms.ModelForm):
    """Form for creating/editing playbooks with inline content editing"""
    
    playbook_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 20,
            'class': 'form-control',
            'placeholder': '---\n- name: My Playbook\n  hosts: all\n  tasks:\n    - name: Example task\n      debug:\n        msg: "Hello World"',
            'style': 'font-family: monospace; font-size: 14px;'
        }),
        help_text='Playbook YAML content (will be saved to file)',
        required=True
    )
    
    class Meta:
        model = Playbook
        fields = ['name', 'description', 'playbook_type', 'os_family', 'playbook_content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Playbook name (without .yml extension)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of what the playbook does'}),
            'playbook_type': forms.Select(attrs={'class': 'form-control'}),
            'os_family': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Playbook Name',
            'description': 'Description',
            'playbook_type': 'Type',
            'os_family': 'OS Family',
        }
        help_texts = {
            'playbook_type': 'Select "Host" for playbooks that run on individual hosts, or "Group" for playbooks that run on groups of hosts.',
            'os_family': 'Select the operating system family this playbook is designed for.',
        }
    
    def __init__(self, *args, **kwargs):
        # Extract playbook_content if editing existing playbook
        instance = kwargs.get('instance')
        if instance and instance.pk:
            if os.path.exists(instance.file.path):
                with open(instance.file.path, 'r') as f:
                    initial = kwargs.get('initial', {})
                    initial['playbook_content'] = f.read()
                    kwargs['initial'] = initial
        
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        """Validate playbook name"""
        name = self.cleaned_data['name']
        # Remove any file extensions if user added them
        if name.endswith('.yml') or name.endswith('.yaml'):
            name = name.rsplit('.', 1)[0]
        return name
    
    def clean_playbook_content(self):
        """Validate YAML syntax"""
        content = self.cleaned_data['playbook_content']
        try:
            # Try to parse YAML to validate syntax
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise forms.ValidationError(f'Invalid YAML syntax: {str(e)}')
        return content
    
    def save(self, commit=True):
        """Save the playbook and write content to file"""
        from django.core.files.base import ContentFile
        
        playbook = super().save(commit=False)
        
        if commit:
            # Create filename
            filename = f"{playbook.name}.yml"
            playbook_content = self.cleaned_data['playbook_content']
            
            # Save file content
            playbook.file.save(filename, ContentFile(playbook_content.encode('utf-8')), save=False)
            playbook.save()
        
        return playbook
