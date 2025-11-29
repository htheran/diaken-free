from django import forms


class CleanupStuckDeploymentsForm(forms.Form):
    timeout_hours = forms.IntegerField(
        label='Timeout (hours)',
        initial=6,
        min_value=1,
        max_value=48,
        help_text='Deployments running longer than this will be marked as failed',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 150px;'})
    )
    
    dry_run = forms.BooleanField(
        label='Dry Run (preview only)',
        required=False,
        initial=True,
        help_text='Check this to see what would be done without actually doing it',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
