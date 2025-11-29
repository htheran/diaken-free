from django import forms
from .models import Script


class ScriptForm(forms.ModelForm):
    """Form for creating/editing scripts"""
    
    script_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 20,
            'class': 'form-control',
            'placeholder': 'Enter your script content here...',
            'style': 'font-family: monospace; font-size: 14px;'
        }),
        help_text='Script content (will be saved to file)',
        required=True
    )
    
    class Meta:
        model = Script
        fields = ['name', 'description', 'target_type', 'os_family', 'active', 'script_content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Script name (without extension)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of what the script does'}),
            'target_type': forms.Select(attrs={'class': 'form-control'}),
            'os_family': forms.Select(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract script_content if editing existing script
        instance = kwargs.get('instance')
        if instance and instance.pk:
            import os
            if os.path.exists(instance.file_path):
                with open(instance.file_path, 'r') as f:
                    initial = kwargs.get('initial', {})
                    initial['script_content'] = f.read()
                    kwargs['initial'] = initial
        
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        """Validate script name"""
        name = self.cleaned_data['name']
        # Remove any file extensions if user added them
        if name.endswith('.sh') or name.endswith('.ps1'):
            name = name.rsplit('.', 1)[0]
        return name
    
    def save(self, commit=True):
        """Save the script and write content to file"""
        import os
        
        script = super().save(commit=False)
        
        if commit:
            script.save()
            
            # Ensure directory exists
            directory = script.get_directory_path()
            os.makedirs(directory, exist_ok=True)
            
            # Write script content to file
            script_content = self.cleaned_data['script_content']
            with open(script.file_path, 'w') as f:
                f.write(script_content)
            
            # Set executable permissions for bash scripts
            if script.os_family in ['redhat', 'debian']:
                os.chmod(script.file_path, 0o755)
        
        return script


class ScriptUploadForm(forms.ModelForm):
    """Form for uploading script files"""
    
    script_file = forms.FileField(
        help_text='Upload a script file (.sh for Linux, .ps1 for Windows)',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.sh,.ps1'})
    )
    
    class Meta:
        model = Script
        fields = ['name', 'description', 'target_type', 'os_family', 'active', 'script_file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Script name (without extension)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of what the script does'}),
            'target_type': forms.Select(attrs={'class': 'form-control'}),
            'os_family': forms.Select(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_script_file(self):
        """Validate uploaded file"""
        script_file = self.cleaned_data['script_file']
        os_family = self.data.get('os_family')
        
        # Check file extension
        filename = script_file.name
        if os_family == 'windows' and not filename.endswith('.ps1'):
            raise forms.ValidationError('Windows scripts must have .ps1 extension')
        elif os_family in ['redhat', 'debian'] and not filename.endswith('.sh'):
            raise forms.ValidationError('Linux scripts must have .sh extension')
        
        return script_file
    
    def clean_name(self):
        """Validate script name"""
        name = self.cleaned_data['name']
        # Remove any file extensions if user added them
        if name.endswith('.sh') or name.endswith('.ps1'):
            name = name.rsplit('.', 1)[0]
        return name
    
    def save(self, commit=True):
        """Save the script and write uploaded file content"""
        import os
        
        script = super().save(commit=False)
        
        if commit:
            script.save()
            
            # Ensure directory exists
            directory = script.get_directory_path()
            os.makedirs(directory, exist_ok=True)
            
            # Write uploaded file content
            script_file = self.cleaned_data['script_file']
            with open(script.file_path, 'wb') as f:
                for chunk in script_file.chunks():
                    f.write(chunk)
            
            # Set executable permissions for bash scripts
            if script.os_family in ['redhat', 'debian']:
                os.chmod(script.file_path, 0o755)
        
        return script
