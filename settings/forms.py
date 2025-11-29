from django import forms
from .models import GlobalSetting, DeploymentCredential, SSLCertificate, VCenterCredential, SettingSection, AnsibleTemplate

class GlobalSettingForm(forms.ModelForm):
    class Meta:
        model = GlobalSetting
        fields = ['section', 'key', 'value', 'description', 'order']
        widgets = {
            'section': forms.Select(attrs={'class': 'form-control w-100'}),
            'key': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'value': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2}),
            'order': forms.NumberInput(attrs={'class': 'form-control w-100'}),
        }
    
    def clean_value(self):
        value = self.cleaned_data.get('value')
        
        # Get key from cleaned_data or from instance if editing
        key = self.cleaned_data.get('key')
        if not key and self.instance and self.instance.pk:
            key = self.instance.key
        
        # Validate snapshot_retention_hours
        if key == 'snapshot_retention_hours':
            try:
                hours = int(value)
                if hours < 1 or hours > 99:
                    raise forms.ValidationError('Snapshot retention must be between 1 and 99 hours')
            except ValueError:
                raise forms.ValidationError('Snapshot retention must be a valid number')
        
        return value

class SettingSectionForm(forms.ModelForm):
    class Meta:
        model = SettingSection
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2}),
        }

class DeploymentCredentialForm(forms.ModelForm):
    class Meta:
        model = DeploymentCredential
        fields = ['name', 'user', 'ssh_key_file', 'ssh_private_key', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'user': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'ssh_key_file': forms.ClearableFileInput(attrs={'class': 'form-control w-100'}),
            'ssh_private_key': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 4, 'placeholder': 'O pega la llave privada SSH aquí (opcional si subes archivo)'}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2}),
        }
        labels = {
            'ssh_key_file': 'Archivo de llave SSH (.pem, .key)',
            'ssh_private_key': 'O pega la llave privada SSH',
        }

class SSLCertificateForm(forms.ModelForm):
    class Meta:
        model = SSLCertificate
        fields = ['name', 'cert_file', 'key_file', 'provider_file', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control w-100', 'placeholder': 'e.g., example.com'}),
            'cert_file': forms.FileInput(attrs={'class': 'form-control w-100', 'accept': '.crt,.pem'}),
            'key_file': forms.FileInput(attrs={'class': 'form-control w-100', 'accept': '.key'}),
            'provider_file': forms.FileInput(attrs={'class': 'form-control w-100', 'accept': '.crt,.pem'}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2, 'placeholder': 'Optional description'}),
        }
        labels = {
            'name': 'Certificate Name',
            'cert_file': 'Certificate File (.crt)',
            'key_file': 'Private Key File (.key)',
            'provider_file': 'Provider/CA Bundle (.crt)',
            'description': 'Description',
        }

from django.utils.translation import gettext_lazy as _

class VCenterCredentialForm(forms.ModelForm):
    class Meta:
        model = VCenterCredential
        fields = ['name', 'host', 'user', 'password', 'ssl_verify', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control w-100', 'placeholder': 'e.g., Production vCenter, Lab vCenter'}),
            'host': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'user': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'password': forms.PasswordInput(render_value=True, attrs={'class': 'form-control w-100', 'autocomplete': 'new-password'}),
            'ssl_verify': forms.CheckboxInput(attrs={'class': ''}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2}),
        }
        labels = {
            'name': _('Name'),
            'host': _('Host'),
            'user': _('User'),
            'password': _('Password'),
            'ssl_verify': _('SSL Verify'),
            'description': _('Description'),
        }

class AnsibleTemplateForm(forms.ModelForm):
    class Meta:
        model = AnsibleTemplate
        fields = ['name', 'description', 'template_type', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Template name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optional)'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.j2,.jinja2'}),
        }
        labels = {
            'name': 'Template Name',
            'description': 'Description',
            'template_type': 'Type',
            'file': 'Template File (.j2 or .jinja2)',
        }
