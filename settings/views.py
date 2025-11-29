from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import GlobalSetting, DeploymentCredential, SSLCertificate, VCenterCredential, SettingSection
from .forms import GlobalSettingForm, DeploymentCredentialForm, SSLCertificateForm, VCenterCredentialForm, SettingSectionForm

# --- Global Settings ---
@login_required
def global_setting_list(request):
    sections = SettingSection.objects.prefetch_related('settings').all()
    return render(request, 'settings/global_setting_list.html', {'sections': sections})

@login_required
def global_setting_create(request):
    if request.method == 'POST':
        form = GlobalSettingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('global_setting_list')
    else:
        form = GlobalSettingForm()
    return render(request, 'settings/global_setting_form.html', {'form': form})

@login_required
def global_setting_update(request, pk):
    setting = get_object_or_404(GlobalSetting, pk=pk)
    if request.method == 'POST':
        form = GlobalSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            return redirect('global_setting_list')
    else:
        form = GlobalSettingForm(instance=setting)
    return render(request, 'settings/global_setting_form.html', {'form': form, 'setting': setting})

@login_required
def global_setting_delete(request, pk):
    setting = get_object_or_404(GlobalSetting, pk=pk)
    if request.method == 'POST':
        setting.delete()
        return redirect('global_setting_list')
    return render(request, 'settings/global_setting_confirm_delete.html', {'setting': setting})

# --- SettingSection ---
@login_required
def section_create(request):
    if request.method == 'POST':
        form = SettingSectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('global_setting_list')
    else:
        form = SettingSectionForm()
    return render(request, 'settings/section_form.html', {'form': form})

@login_required
def section_update(request, pk):
    section = get_object_or_404(SettingSection, pk=pk)
    if request.method == 'POST':
        form = SettingSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            return redirect('global_setting_list')
    else:
        form = SettingSectionForm(instance=section)
    return render(request, 'settings/section_form.html', {'form': form, 'section': section})

@login_required
def section_delete(request, pk):
    section = get_object_or_404(SettingSection, pk=pk)
    if request.method == 'POST':
        section.delete()
        return redirect('global_setting_list')
    return render(request, 'settings/section_confirm_delete.html', {'section': section})

# --- Deployment Credentials ---
@login_required
def credential_list(request):
    credentials = DeploymentCredential.objects.all()
    return render(request, 'settings/credential_list.html', {'credentials': credentials})

@login_required
def credential_create(request):
    if request.method == 'POST':
        form = DeploymentCredentialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('credential_list')
    else:
        form = DeploymentCredentialForm()
    return render(request, 'settings/credential_form.html', {'form': form})

@login_required
def credential_update(request, pk):
    credential = get_object_or_404(DeploymentCredential, pk=pk)
    if request.method == 'POST':
        form = DeploymentCredentialForm(request.POST, request.FILES, instance=credential)
        if form.is_valid():
            form.save()
            return redirect('credential_list')
    else:
        form = DeploymentCredentialForm(instance=credential)
    return render(request, 'settings/credential_form.html', {'form': form, 'credential': credential})

@login_required
def credential_delete(request, pk):
    credential = get_object_or_404(DeploymentCredential, pk=pk)
    if request.method == 'POST':
        credential.delete()
        return redirect('credential_list')
    return render(request, 'settings/credential_confirm_delete.html', {'credential': credential})

# --- SSL Certificates ---
@login_required
def ssl_certificate_list(request):
    certificates = SSLCertificate.objects.all().order_by('name')
    return render(request, 'settings/ssl_certificate_list.html', {'certificates': certificates})

@login_required
def ssl_certificate_create(request):
    if request.method == 'POST':
        form = SSLCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('ssl_certificate_list')
    else:
        form = SSLCertificateForm()
    return render(request, 'settings/ssl_certificate_form.html', {'form': form})

@login_required
def ssl_certificate_update(request, pk):
    certificate = get_object_or_404(SSLCertificate, pk=pk)
    if request.method == 'POST':
        form = SSLCertificateForm(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            form.save()
            return redirect('ssl_certificate_list')
    else:
        form = SSLCertificateForm(instance=certificate)
    return render(request, 'settings/ssl_certificate_form.html', {'form': form, 'certificate': certificate})

@login_required
def ssl_certificate_delete(request, pk):
    certificate = get_object_or_404(SSLCertificate, pk=pk)
    if request.method == 'POST':
        certificate.delete()
        return redirect('ssl_certificate_list')
    return redirect('ssl_certificate_list')

# --- vCenter Credentials ---
@login_required
def vcenter_credential_list(request):
    creds = VCenterCredential.objects.all()
    return render(request, 'settings/vcenter_credential_list.html', {'creds': creds})

@login_required
def vcenter_credential_create(request):
    if request.method == 'POST':
        form = VCenterCredentialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('vcenter_credential_list')
    else:
        form = VCenterCredentialForm()
    return render(request, 'settings/vcenter_credential_form.html', {'form': form})

@login_required
def vcenter_credential_update(request, pk):
    cred = get_object_or_404(VCenterCredential, pk=pk)
    if request.method == 'POST':
        form = VCenterCredentialForm(request.POST, instance=cred)
        if form.is_valid():
            form.save()
            return redirect('vcenter_credential_list')
    else:
        form = VCenterCredentialForm(instance=cred)
    return render(request, 'settings/vcenter_credential_form.html', {'form': form, 'cred': cred})

@login_required
def vcenter_credential_delete(request, pk):
    cred = get_object_or_404(VCenterCredential, pk=pk)
    if request.method == 'POST':
        cred_name = cred.name
        cred.delete()  # Hard delete from database
        messages.success(request, f'vCenter credential "{cred_name}" deleted successfully.')
        return redirect('vcenter_credential_list')
    return render(request, 'settings/vcenter_credential_confirm_delete.html', {'cred': cred})

# --- Ansible Templates ---
@login_required
def template_list(request):
    from .models import AnsibleTemplate
    templates = AnsibleTemplate.objects.all()
    return render(request, 'settings/template_list.html', {'templates': templates})

@login_required
def template_upload(request):
    from .forms import AnsibleTemplateForm
    if request.method == 'POST':
        form = AnsibleTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('template_list')
    else:
        form = AnsibleTemplateForm()
    return render(request, 'settings/template_upload.html', {'form': form})

@login_required
def template_edit(request, pk):
    from .models import AnsibleTemplate
    from .forms import AnsibleTemplateForm
    template = get_object_or_404(AnsibleTemplate, pk=pk)
    if request.method == 'POST':
        form = AnsibleTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            return redirect('template_list')
    else:
        form = AnsibleTemplateForm(instance=template)
    return render(request, 'settings/template_edit.html', {'form': form, 'template': template})

@login_required
def template_delete(request, pk):
    from .models import AnsibleTemplate
    template = get_object_or_404(AnsibleTemplate, pk=pk)
    if request.method == 'POST':
        template.delete()
        return redirect('template_list')
    return render(request, 'settings/template_delete.html', {'template': template})

# Create your views here.

# --- Export/Import Global Settings ---
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.http import require_http_methods

@login_required
def export_global_settings(request):
    """Export all global settings to JSON file"""
    # Prepare data structure
    export_data = {
        'version': '1.0',
        'exported_at': timezone.now().isoformat(),
        'sections': {},
        'settings_without_section': []
    }
    
    # Export sections with their settings
    for section in SettingSection.objects.all():
        export_data['sections'][section.name] = {
            'description': section.description,
            'settings': []
        }
        
        for setting in section.settings.all().order_by('order'):
            export_data['sections'][section.name]['settings'].append({
                'key': setting.key,
                'value': setting.value,
                'description': setting.description,
                'order': setting.order
            })
    
    # Export settings without section
    for setting in GlobalSetting.objects.filter(section__isnull=True).order_by('order'):
        export_data['settings_without_section'].append({
            'key': setting.key,
            'value': setting.value,
            'description': setting.description,
            'order': setting.order
        })
    
    # Create JSON response
    response = HttpResponse(
        json.dumps(export_data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="diaken_settings_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    messages.success(request, 'Settings exported successfully')
    return response


@login_required
@require_http_methods(["GET", "POST"])
def import_global_settings(request):
    """Import global settings from JSON file"""
    if request.method == 'POST':
        if 'settings_file' not in request.FILES:
            messages.error(request, 'No file uploaded')
            return redirect('global_setting_list')
        
        uploaded_file = request.FILES['settings_file']
        
        # Validate file extension
        if not uploaded_file.name.endswith('.json'):
            messages.error(request, 'Invalid file format. Please upload a JSON file.')
            return redirect('global_setting_list')
        
        try:
            # Read and parse JSON
            file_content = uploaded_file.read().decode('utf-8')
            import_data = json.loads(file_content)
            
            # Validate structure
            if 'version' not in import_data:
                messages.error(request, 'Invalid file structure. Missing version field.')
                return redirect('global_setting_list')
            
            # Statistics
            stats = {
                'sections_created': 0,
                'sections_skipped': 0,
                'settings_created': 0,
                'settings_skipped': 0,
                'settings_updated': 0
            }
            
            # Import sections
            if 'sections' in import_data:
                for section_name, section_data in import_data['sections'].items():
                    # Check if section exists
                    section, created = SettingSection.objects.get_or_create(
                        name=section_name,
                        defaults={'description': section_data.get('description', '')}
                    )
                    
                    if created:
                        stats['sections_created'] += 1
                    else:
                        stats['sections_skipped'] += 1
                    
                    # Import settings for this section
                    for setting_data in section_data.get('settings', []):
                        key = setting_data['key']
                        
                        # Check if setting exists
                        existing = GlobalSetting.objects.filter(key=key).first()
                        
                        if existing:
                            # Setting exists - skip or update based on user preference
                            stats['settings_skipped'] += 1
                        else:
                            # Create new setting
                            GlobalSetting.objects.create(
                                section=section,
                                key=key,
                                value=setting_data['value'],
                                description=setting_data.get('description', ''),
                                order=setting_data.get('order', 0)
                            )
                            stats['settings_created'] += 1
            
            # Import settings without section (acepta null o array)
            if 'settings_without_section' in import_data:
                sws = import_data['settings_without_section']
                if sws is None:
                    sws = []
                for setting_data in sws:
                    key = setting_data['key']
                    existing = GlobalSetting.objects.filter(key=key).first()
                    if existing:
                        stats['settings_skipped'] += 1
                    else:
                        GlobalSetting.objects.create(
                            section=None,
                            key=key,
                            value=setting_data['value'],
                            description=setting_data.get('description', ''),
                            order=setting_data.get('order', 0)
                        )
                        stats['settings_created'] += 1
            
            # Build success message
            msg_parts = []
            if stats['sections_created'] > 0:
                msg_parts.append(f"{stats['sections_created']} section(s) created")
            if stats['sections_skipped'] > 0:
                msg_parts.append(f"{stats['sections_skipped']} section(s) already existed")
            if stats['settings_created'] > 0:
                msg_parts.append(f"{stats['settings_created']} setting(s) imported")
            if stats['settings_skipped'] > 0:
                msg_parts.append(f"{stats['settings_skipped']} setting(s) skipped (already exist)")
            
            if msg_parts:
                messages.success(request, 'Import completed: ' + ', '.join(msg_parts))
            else:
                messages.warning(request, 'No new settings were imported. All variables already exist or file is empty.')
            
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON file format')
        except Exception as e:
            messages.error(request, f'Error importing settings: {str(e)}')
        
        return redirect('global_setting_list')
    
    # GET request - show import form
    return render(request, 'settings/global_setting_import.html')
