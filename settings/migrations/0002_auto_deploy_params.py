from django.db import migrations

def add_deploy_params(apps, schema_editor):
    SettingSection = apps.get_model('settings', 'SettingSection')
    GlobalSetting = apps.get_model('settings', 'GlobalSetting')
    
    # Create default section first
    section, created = SettingSection.objects.get_or_create(
        id=1,
        defaults={'name': 'Deployment', 'description': 'Deployment settings'}
    )
    
    # Now create settings
    GlobalSetting.objects.get_or_create(key='vcenter_template', defaults={'value': 'plantilla9.6', 'section_id': section.id})
    GlobalSetting.objects.get_or_create(key='deploy_env', defaults={'value': 'NEWS', 'section_id': section.id})
    GlobalSetting.objects.get_or_create(key='deploy_group', defaults={'value': 'NEWS', 'section_id': section.id})
    GlobalSetting.objects.get_or_create(key='vcenter_host', defaults={'value': 'vcsa.local', 'section_id': section.id})
    GlobalSetting.objects.get_or_create(key='vcenter_user', defaults={'value': 'administrator@vsphere.local', 'section_id': section.id})
    GlobalSetting.objects.get_or_create(key='vcenter_password', defaults={'value': 'changeme', 'section_id': section.id})

class Migration(migrations.Migration):
    dependencies = [
        ('settings', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(add_deploy_params),
    ]
