# Windows Deployment Libraries

## Required Python Libraries

### Core Dependencies

#### 1. **pywinrm** (0.5.0)
- **Purpose**: Python library for Windows Remote Management (WinRM)
- **Usage**: Connect to Windows Server via WinRM protocol
- **Installation**: `pip install pywinrm`
- **Dependencies**:
  - requests >= 2.9.1
  - xmltodict
  - requests-ntlm

#### 2. **requests-ntlm** (1.3.0)
- **Purpose**: NTLM authentication for requests
- **Usage**: Authenticate with Windows Server using NTLM
- **Installation**: `pip install requests-ntlm`
- **Dependencies**:
  - cryptography >= 1.3
  - pyspnego >= 0.4.0

#### 3. **requests-credssp** (2.0.0)
- **Purpose**: CredSSP authentication for requests
- **Usage**: Alternative authentication method for WinRM
- **Installation**: `pip install pywinrm[credssp]`

#### 4. **pyvmomi** (9.0.0.0)
- **Purpose**: Python SDK for VMware vSphere API
- **Usage**: Clone VMs, manage vCenter resources
- **Installation**: `pip install pyvmomi`
- **Note**: Already installed for Linux deployment

#### 5. **cryptography** (46.0.2)
- **Purpose**: Cryptographic recipes and primitives
- **Usage**: Secure authentication and encryption
- **Installation**: Automatically installed with requests-ntlm

#### 6. **pyspnego** (0.12.0)
- **Purpose**: SPNEGO authentication library
- **Usage**: Windows authentication protocols
- **Installation**: Automatically installed with requests-ntlm

#### 7. **xmltodict** (1.0.2)
- **Purpose**: XML to Python dict converter
- **Usage**: Parse WinRM XML responses
- **Installation**: Automatically installed with pywinrm

---

## Ansible Collections

### 1. **ansible.windows** (1.14.0)
- **Purpose**: Core Windows modules for Ansible
- **Installation**: `ansible-galaxy collection install ansible.windows`
- **Modules Used**:
  - `win_hostname`: Change Windows hostname
  - `win_shell`: Execute PowerShell commands
  - `win_reboot`: Reboot Windows Server
  - `wait_for_connection`: Wait for WinRM availability

### 2. **community.windows** (1.13.0)
- **Purpose**: Community-maintained Windows modules
- **Installation**: `ansible-galaxy collection install community.windows`
- **Modules Available**:
  - `win_domain_join`: Join Active Directory
  - `win_feature`: Install Windows features
  - `win_iis_*`: IIS management
  - `win_dns_*`: DNS management

---

## Installation Commands

### Quick Install (All at once)
```bash
# Install Python libraries
pip install pywinrm pywinrm[credssp] requests-ntlm

# Install Ansible collections
ansible-galaxy collection install ansible.windows
ansible-galaxy collection install community.windows
```

### Individual Install
```bash
# Core WinRM
pip install pywinrm

# CredSSP support (optional)
pip install pywinrm[credssp]

# NTLM support
pip install requests-ntlm

# Ansible Windows modules
ansible-galaxy collection install ansible.windows
ansible-galaxy collection install community.windows
```

---

## Verification

### Check Python Libraries
```bash
pip list | grep -E "(pywinrm|pyvmomi|requests|xmltodict)"
```

Expected output:
```
cryptography       46.0.2
pyspnego           0.12.0
pyvmomi            9.0.0.0
pywinrm            0.5.0
requests           2.32.5
requests-credssp   2.0.0
requests_ntlm      1.3.0
xmltodict          1.0.2
```

### Check Ansible Collections
```bash
ansible-galaxy collection list | grep windows
```

Expected output:
```
ansible.windows               1.14.0
community.windows             1.13.0
```

### Test WinRM Connection
```python
import winrm

session = winrm.Session(
    'http://10.100.18.85:5985/wsman',
    auth=('administrator', 'password'),
    transport='ntlm'
)

result = session.run_cmd('hostname')
print(result.std_out.decode())
```

---

## Library Usage in Diaken

### 1. **views_windows.py**
```python
import winrm  # WinRM connection
from pyVim.connect import SmartConnect, Disconnect  # vCenter
from pyVmomi import vim  # vSphere objects
```

### 2. **provision_windows_vm.yml**
```yaml
- name: Customize Windows Server VM
  hosts: all
  gather_facts: no
  vars:
    ansible_connection: winrm  # Uses pywinrm
    ansible_winrm_transport: ntlm  # Uses requests-ntlm
```

---

## Troubleshooting

### Issue: "No module named 'winrm'"
**Solution**: `pip install pywinrm`

### Issue: "NTLM authentication failed"
**Solution**: 
1. Check Windows credentials
2. Verify WinRM is enabled on target
3. Install: `pip install requests-ntlm`

### Issue: "SSL certificate verification failed"
**Solution**: Use `server_cert_validation='ignore'` in Session

### Issue: "Connection timeout"
**Solution**:
1. Check firewall (port 5985/5986)
2. Verify WinRM service is running
3. Test with: `Test-WSMan <ip>` from PowerShell

---

## Security Considerations

### Production Recommendations:
1. **Use HTTPS (port 5986)** instead of HTTP (port 5985)
2. **Use CredSSP or Kerberos** instead of Basic auth
3. **Enable certificate validation** in production
4. **Encrypt passwords** in database
5. **Use domain accounts** with minimal privileges

### Development Setup (Current):
- Protocol: HTTP (port 5985)
- Auth: NTLM
- Cert validation: Disabled
- Credentials: Stored in database

---

## Performance Notes

- **WinRM is slower than SSH**: Windows boot time ~120s vs Linux ~60s
- **PowerShell execution**: Adds overhead compared to bash
- **Network latency**: WinRM uses more round-trips than SSH
- **Memory usage**: pywinrm uses more memory than paramiko

---

## Compatibility

### Python Versions:
- ✓ Python 3.9+
- ✓ Python 3.12 (current)

### Windows Versions:
- ✓ Windows Server 2012 R2+
- ✓ Windows Server 2016
- ✓ Windows Server 2019
- ✓ Windows Server 2022 (tested)

### Ansible Versions:
- ✓ Ansible 2.9+
- ✓ Ansible 2.14.18 (current)

---

## References

- pywinrm: https://github.com/diyan/pywinrm
- pyvmomi: https://github.com/vmware/pyvmomi
- ansible.windows: https://docs.ansible.com/ansible/latest/collections/ansible/windows/
- WinRM Protocol: https://docs.microsoft.com/en-us/windows/win32/winrm/portal

---

**Last Updated**: 2025-10-06
**Status**: ✅ All libraries installed and verified
