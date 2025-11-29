from django import forms

from settings.models import DeploymentCredential
from playbooks.models import Playbook

class DeployVMForm(forms.Form):
    vcenter = forms.ChoiceField(label='vCenter', choices=[], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    datacenter = forms.ChoiceField(label='Datacenter', choices=[], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    ssh_credential = forms.ChoiceField(
        label='Credencial SSH',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control w-100'})
    )
    cluster = forms.ChoiceField(label='Cluster', choices=[], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    resource_pool = forms.ChoiceField(label='Resource Pool', choices=[], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    datastore = forms.ChoiceField(label='Datastore', choices=[], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    network = forms.ChoiceField(label='Network', choices=[], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    template = forms.ChoiceField(label='Template', choices=[], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    hostname = forms.CharField(label='Hostname', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control w-100'}))
    ip = forms.GenericIPAddressField(label='IP Address', widget=forms.TextInput(attrs={'class': 'form-control w-100'}))
    operating_system = forms.ChoiceField(label='Operating System', choices=[('redhat', 'RedHat/CentOS'), ('debian', 'Debian/Ubuntu')], widget=forms.Select(attrs={'class': 'form-control w-100'}))
    additional_playbook = forms.CharField(
        label='Additional Playbook',
        required=False,
        widget=forms.HiddenInput()  # Hidden field, populated by JavaScript
    )
    ansible_python_interpreter = forms.CharField(
        label='Ansible Python Interpreter',
        initial='/usr/bin/python3',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control w-100', 'placeholder': '/usr/bin/python3'})
    )
