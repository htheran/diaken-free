#!/usr/bin/env python
"""
Compare WinRM configurations between deployment and playbook execution
"""
import os
import sys
import django

sys.path.insert(0, '/opt/www/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

from inventory.models import Host
from settings.models import WindowsCredential

def compare_configs(hostname):
    try:
        host = Host.objects.get(name=hostname)
        
        print("="*70)
        print(f"WinRM Configuration Comparison for: {host.name}")
        print("="*70)
        print(f"IP: {host.ip}")
        print(f"OS: {host.operating_system}")
        print()
        
        if not host.windows_credential:
            print("❌ ERROR: No Windows credential configured")
            return
        
        cred = host.windows_credential
        
        print("DEPLOYMENT INVENTORY FORMAT (views_windows.py):")
        print("-"*70)
        deployment_inv = f"""[windows]
{host.ip}

[windows:vars]
ansible_user={cred.username}
ansible_password={cred.password}
ansible_connection=winrm
ansible_winrm_transport={cred.auth_type}
ansible_winrm_server_cert_validation=ignore
ansible_port={cred.get_port()}
"""
        print(deployment_inv)
        
        print("\nPLAYBOOK EXECUTION INVENTORY FORMAT (views_playbook_windows.py):")
        print("-"*70)
        playbook_inv = f"""[windows_hosts]
{host.ip} ansible_user={cred.username} ansible_password={cred.password} ansible_connection=winrm ansible_winrm_transport={cred.auth_type} ansible_winrm_server_cert_validation=ignore ansible_port={cred.get_port()} ansible_winrm_read_timeout_sec=60 ansible_winrm_operation_timeout_sec=50
"""
        print(playbook_inv)
        
        print("\nDIFFERENCES:")
        print("-"*70)
        print("1. Group name:")
        print("   Deployment:  [windows]")
        print("   Playbook:    [windows_hosts]")
        print()
        print("2. Variable format:")
        print("   Deployment:  [windows:vars] section")
        print("   Playbook:    Inline variables")
        print()
        print("3. Additional timeouts in Playbook:")
        print("   ansible_winrm_read_timeout_sec=60")
        print("   ansible_winrm_operation_timeout_sec=50")
        print()
        
        print("\nCREDENTIALS:")
        print("-"*70)
        print(f"Username: {cred.username}")
        print(f"Password: {'*' * len(cred.password)}")
        print(f"Domain: {cred.domain or 'N/A'}")
        print(f"Auth Type: {cred.auth_type}")
        print(f"Port: {cred.get_port()}")
        print(f"HTTPS: {cred.use_https}")
        print()
        
        print("\nRECOMMENDATIONS:")
        print("-"*70)
        print("1. Test with deployment-style inventory:")
        print(f"   cat > /tmp/test_deploy_style.ini << 'EOF'")
        print(deployment_inv.strip())
        print("EOF")
        print(f"   ansible windows -i /tmp/test_deploy_style.ini -m win_ping -vvv")
        print()
        print("2. Test with playbook-style inventory:")
        print(f"   cat > /tmp/test_playbook_style.ini << 'EOF'")
        print(playbook_inv.strip())
        print("EOF")
        print(f"   ansible windows_hosts -i /tmp/test_playbook_style.ini -m win_ping -vvv")
        print()
        print("3. If deployment style works but playbook style doesn't:")
        print("   - Issue is with inline variable format")
        print("   - Solution: Use [windows_hosts:vars] format in playbook execution")
        print()
        print("4. If neither works:")
        print("   - WinRM configuration changed after deployment")
        print("   - Check if password was changed")
        print("   - Check if WinRM was disabled")
        print("   - Verify with: python test_winrm_connection.py", hostname)
        
    except Host.DoesNotExist:
        print(f"❌ ERROR: Host '{hostname}' not found")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        hostname = sys.argv[1]
    else:
        print("Available Windows hosts:")
        hosts = Host.objects.filter(operating_system='windows', active=True)
        for h in hosts:
            print(f"  - {h.name} ({h.ip})")
        
        if hosts.exists():
            hostname = input("\nEnter hostname to compare: ").strip()
        else:
            print("\n❌ No Windows hosts found")
            sys.exit(1)
    
    compare_configs(hostname)
