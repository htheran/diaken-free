from django import forms
from .models import Environment, Group, Host
from settings.models import DeploymentCredential, WindowsCredential

class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment
        fields = ['name', 'description', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 3}),
            'active': forms.CheckboxInput(attrs={'class': ''}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'environment', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 3}),
            'environment': forms.Select(attrs={'class': 'form-control w-100'}),
            'active': forms.CheckboxInput(attrs={'class': ''}),
        }

class HostForm(forms.ModelForm):
    class Meta:
        model = Host
        fields = ['name', 'ip', 'vcenter_server', 'environment', 'group', 'operating_system', 'ansible_python_interpreter', 'deployment_credential', 'windows_credential', 'status', 'tags', 'notes', 'description', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'ip': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'environment': forms.Select(attrs={'class': 'form-control w-100'}),
            'group': forms.Select(attrs={'class': 'form-control w-100'}),
            'operating_system': forms.Select(attrs={'class': 'form-control w-100', 'id': 'id_operating_system'}),
            'ansible_python_interpreter': forms.TextInput(attrs={'class': 'form-control w-100', 'id': 'id_ansible_python_interpreter'}),
            'deployment_credential': forms.Select(attrs={'class': 'form-control w-100', 'id': 'id_deployment_credential'}),
            'windows_credential': forms.Select(attrs={'class': 'form-control w-100', 'id': 'id_windows_credential'}),
            'status': forms.HiddenInput(),
            'tags': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'notes': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2}),
            'description': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2}),
            'active': forms.CheckboxInput(attrs={'class': ''}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['deployment_credential'].queryset = DeploymentCredential.objects.all().order_by('name')
        self.fields['windows_credential'].queryset = WindowsCredential.objects.all().order_by('name')
        # Make vcenter_server optional (for Proxmox, standalone VMs, etc.)
        self.fields['vcenter_server'].required = False
