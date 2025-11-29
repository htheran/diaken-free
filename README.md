# 🚀 Diaken - Automated VM Deployment & Infrastructure Management System

[![Django](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Ansible](https://img.shields.io/badge/Ansible-2.14+-red.svg)](https://www.ansible.com/)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)]()

Professional automated virtual machine deployment system with complete vCenter and Ansible integration. Manage your entire infrastructure lifecycle from a single web interface.

## 🔒 Security Status

**Security Score:** 🟢 **9.0/10** - Production Ready

✅ **All Critical Vulnerabilities Fixed** (October 16, 2025)
- ✅ SECRET_KEY from environment variables
- ✅ ALLOWED_HOSTS properly configured
- ✅ Credentials encrypted with Fernet (AES-128)
- ✅ Full CSRF protection enabled
- ✅ Input sanitization implemented
- ✅ XSS prevention in place

📄 **Security Documentation:** See [`SECURITY_FIXES_IMPLEMENTED.md`](SECURITY_FIXES_IMPLEMENTED.md) and [`docs/security_analysis/`](docs/security_analysis/) for complete security analysis.

⚠️ **Important:** Before deployment, configure environment variables in `.env` file. See [Configuration](#-configuration) section.

## ✨ Key Features

### 🖥️ **VM Deployment**
- ✅ Automated VM deployment from vCenter templates
- ✅ Support for Linux (RedHat/Debian) and Windows Server
- ✅ Post-deployment configuration with Ansible
- ✅ Custom playbook execution during deployment
- ✅ Real-time deployment progress monitoring
- ✅ Automatic hostname and IP configuration
- ✅ **Automatic network change** (DVS ↔ Standard, with DirectPath I/O support)
- ✅ **Persistent IP configuration** with nmcli
- ✅ **Automated VM reboot** with post-reboot verification

### 📦 **Playbook Management**
- ✅ Create playbooks with inline YAML editor
- ✅ YAML syntax validation
- ✅ Upload existing playbook files
- ✅ Edit playbooks with live preview
- ✅ Download and backup playbooks
- ✅ Organized by OS family and target type
- ✅ Copy-to-clipboard functionality

### 📜 **Script Management**
- ✅ PowerShell and Bash script repository
- ✅ Inline script editor with syntax highlighting
- ✅ Execute scripts on demand
- ✅ Scheduled script execution
- ✅ Organized by OS and target type
- ✅ Version control and history

### 📅 **Task Scheduler**
- ✅ Schedule playbooks and scripts
- ✅ Recurring tasks (daily, weekly, monthly)
- ✅ One-time scheduled executions
- ✅ Execution history and logs
- ✅ Email notifications on completion
- ✅ Webhook integration

### 📊 **Inventory Management**
- ✅ Complete host inventory with grouping
- ✅ Environment-based organization
- ✅ Support for multiple hypervisors (vCenter, Proxmox, standalone)
- ✅ Automatic SSH fingerprint acceptance
- ✅ Credential management per host
- ✅ Custom Ansible variables

### 📸 **Snapshot Management**
- ✅ Create VM snapshots with descriptions
- ✅ Restore to previous snapshots
- ✅ Delete old snapshots
- ✅ Automatic retention policies
- ✅ Snapshot lifecycle management

### 📈 **History & Monitoring**
- ✅ Complete deployment history
- ✅ Ansible output logs
- ✅ Execution time tracking
- ✅ Success/failure statistics
- ✅ Cleanup of stuck deployments
- ✅ Dashboard with real-time metrics

### 🔔 **Notifications**
- ✅ Email notifications (SMTP)
- ✅ Webhook integrations
- ✅ Deployment status alerts
- ✅ Scheduled task notifications
- ✅ Custom notification templates

### 🔐 **Security & Credentials**
- ✅ SSH key management with validation
- ✅ vCenter credential storage
- ✅ Windows WinRM credentials
- ✅ Deployment credentials per host
- ✅ User authentication and permissions
- ✅ Secure password storage

## 🛠️ Technology Stack

- **Backend**: Django 5.2.6 (Python 3.12)
- **Frontend**: Bootstrap 4, AdminLTE 3, jQuery
- **Automation**: Ansible 2.14+
- **Virtualization**: VMware vSphere API (pyvmomi)
- **Windows Management**: WinRM (pywinrm)
- **Database**: SQLite (development) / PostgreSQL (production)
- **YAML Processing**: PyYAML 6.0.3

## 📋 Requirements

### System Requirements
- **OS**: Oracle Linux 9 / RedHat 9 / CentOS 9 / Ubuntu 22.04+
- **Python**: 3.12+
- **Memory**: 4GB RAM minimum
- **Disk**: 20GB available space
- **Network**: Access to vCenter and target hosts

### Software Dependencies
- Python 3.12+
- Django 5.2.6
- Ansible 2.14+
- VMware vCenter 6.5+ or 7.0+
- SSH access to Linux hosts
- WinRM configured on Windows hosts

## 📦 Installation

### 1. Clone Repository
```bash
cd /opt/www
git clone https://github.com/htheran/diakendev.git app
cd app
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Django
```bash
# Copy settings template (if exists)
cp diaken/settings.py.example diaken/settings.py

# Edit settings as needed
vim diaken/settings.py
```

### 5. Initialize Database
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create example playbook (optional)
python manage.py create_example_playbook
```

### 6. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 7. Start Development Server
```bash
python manage.py runserver 0.0.0.0:8001
```

Access the application at: `http://your-server:8001`

## ⚙️ Configuration

### 1. Global Variables
Navigate to **Settings → Variables** and configure:

```ini
[Default]
deploy_env = PRODUCTION
deploy_group = WEB_SERVERS

[Template Redhat]
ip_template = 10.100.18.80

[Template Debian]
ip_template = 10.100.18.81

[Template Windows]
ip_template = 10.100.18.82

[Update]
log_dir_update = /var/log/ansible_updates
update_package = *

[Paths]
playbook_dir = /opt/www/app/ansible
inventory_dir = /opt/www/app/inventory
```

### 2. SSH Credentials
Navigate to **Settings → Deployment Credentials**:
1. Click **Add Credential**
2. Upload your SSH private key
3. Set permissions automatically (0600)
4. Assign to hosts as needed

### 3. vCenter Configuration
Navigate to **Settings → vCenter**:
1. Click **Add vCenter**
2. Configure:
   - **Name**: Descriptive name
   - **Host**: vcenter.example.com
   - **Username**: administrator@vsphere.local
   - **Password**: Your vCenter password
   - **Port**: 443 (default)
3. Test connection

### 4. Windows Credentials (for WinRM)
Navigate to **Settings → Windows Credentials**:
1. Click **Add Credential**
2. Configure:
   - **Name**: Descriptive name
   - **Username**: Administrator
   - **Password**: Windows password
3. Assign to Windows hosts

### 5. Email Notifications (Optional)
Navigate to **Settings → Email Configuration**:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@example.com'
```

## 🚀 Usage Guide

### Deploy a Linux VM

1. Navigate to **Deploy → Deploy Linux VM**
2. Fill in the form:
   - **vCenter Server**: Select your vCenter
   - **Datacenter**: Select datacenter
   - **Cluster**: Select cluster
   - **Datastore**: Select datastore
   - **Network**: Select network
   - **Template**: Select Linux template
   - **Hostname**: Enter hostname (e.g., web-server-01)
   - **IP Address**: Enter IP (e.g., 10.100.18.100)
   - **SSH Credential**: Select SSH key
   - **OS**: RedHat or Debian
   - **Python Interpreter**: /usr/bin/python3
   - **Post-Deployment Playbooks**: Select optional playbooks
3. Click **Deploy VM**
4. Monitor progress in real-time modal
5. Check deployment history

### Deploy a Windows VM

1. Navigate to **Deploy → Deploy Windows VM**
2. Fill in the form:
   - **vCenter Server**: Select your vCenter
   - **Datacenter**: Select datacenter
   - **Cluster**: Select cluster
   - **Datastore**: Select datastore
   - **Network**: Select network
   - **Template**: Select Windows template
   - **Hostname**: Enter hostname
   - **IP Address**: Enter IP
   - **Windows Credential**: Select WinRM credential
   - **Post-Deployment Scripts**: Select optional scripts
3. Click **Deploy VM**
4. Monitor progress
5. Verify in history

### Manage Playbooks

#### Create New Playbook
1. Navigate to **Playbooks → Create Playbook**
2. Fill in details:
   - **Name**: playbook-name (without .yml)
   - **Description**: What this playbook does
   - **Type**: Host or Group
   - **OS Family**: RedHat, Debian, or Windows
   - **Content**: Write YAML content in editor
3. Click **Save Playbook**
4. YAML syntax is validated automatically

#### Upload Existing Playbook
1. Navigate to **Playbooks → Upload Playbook**
2. Select `.yml` or `.yaml` file
3. Fill in metadata
4. Click **Upload**

#### Edit Playbook
1. Navigate to **Playbooks → List Playbooks**
2. Find your playbook
3. Click **Edit**
4. Modify content or metadata
5. Click **Save**

### Execute Playbooks

#### On Linux Hosts
1. Navigate to **Deploy → Execute Playbook (Linux)**
2. Select:
   - **Target Type**: Host or Group
   - **Target**: Select host/group
   - **Playbook**: Select playbook
3. Click **Execute**
4. View output in real-time

#### On Windows Hosts
1. Navigate to **Deploy → Execute Playbook (Windows)**
2. Select target and playbook
3. Click **Execute**
4. Monitor execution

### Schedule Tasks

1. Navigate to **Scheduler → Scheduled Tasks**
2. Click **Create Task**
3. Configure:
   - **Name**: Task name
   - **Execution Type**: Playbook or Script
   - **Target Type**: Host or Group
   - **Target**: Select target
   - **Playbook/Script**: Select item
   - **Schedule Type**: One-time or Recurring
   - **Date/Time**: When to execute
   - **Recurrence**: Daily, Weekly, Monthly (if recurring)
   - **Email Notification**: Enable if desired
4. Click **Save**
5. Task will execute automatically

### Manage Snapshots

#### Create Snapshot
1. Navigate to **Snapshots → Create Snapshot**
2. Select VM from inventory
3. Enter snapshot name and description
4. Click **Create**

#### Restore Snapshot
1. Navigate to **Snapshots → List Snapshots**
2. Find snapshot
3. Click **Restore**
4. Confirm restoration

#### Delete Snapshot
1. Navigate to **Snapshots → List Snapshots**
2. Find snapshot
3. Click **Delete**
4. Confirm deletion

### Manage Inventory

#### Add Host
1. Navigate to **Inventory → Hosts → Add Host**
2. Fill in details:
   - **Name**: Hostname
   - **IP Address**: Host IP
   - **vCenter Server**: Optional (leave empty for Proxmox/standalone)
   - **Environment**: Select environment
   - **Group**: Select group (optional)
   - **Operating System**: RedHat, Debian, or Windows
   - **Python Interpreter**: Path to Python (Linux only)
   - **Deployment Credential**: Select SSH key (Linux)
   - **Windows Credential**: Select WinRM credential (Windows)
3. Click **Save**
4. SSH fingerprint is accepted automatically

#### Organize with Groups
1. Navigate to **Inventory → Groups**
2. Create groups for organization:
   - Web Servers
   - Database Servers
   - Application Servers
3. Assign hosts to groups

## 📁 Project Structure

```
/opt/www/app/
├── ansible/                    # Ansible playbooks
│   ├── provision_vm.yml       # Linux provisioning
│   └── provision_windows_vm.yml # Windows provisioning
├── dashboard/                  # Dashboard app
├── deploy/                     # Deployment logic
│   ├── views.py               # Linux deployment
│   ├── views_windows.py       # Windows deployment
│   ├── views_playbook.py      # Playbook execution (Linux)
│   └── views_playbook_windows.py # Playbook execution (Windows)
├── docs/                       # Documentation
│   ├── README.md              # This file
│   ├── PLAYBOOK_MANAGEMENT_SYSTEM.md
│   ├── SCHEDULER_README.md
│   ├── USER_MANAGEMENT_GUIDE.md
│   └── ...
├── history/                    # Deployment history
├── inventory/                  # Host inventory management
│   ├── models.py              # Environment, Group, Host models
│   ├── views.py               # CRUD operations
│   └── forms.py               # Forms
├── media/                      # User-uploaded files
│   ├── playbooks/             # Uploaded playbooks
│   │   ├── host/              # Host-specific playbooks
│   │   └── group/             # Group playbooks
│   ├── scripts/               # Uploaded scripts
│   │   ├── bash/              # Bash scripts
│   │   └── powershell/        # PowerShell scripts
│   ├── j2/                    # Jinja2 templates
│   │   ├── host/
│   │   └── group/
│   └── ssh/                   # SSH keys
├── notifications/              # Notification system
├── playbooks/                  # Playbook management app
│   ├── models.py              # Playbook model
│   ├── views.py               # CRUD operations
│   ├── forms.py               # Forms with YAML validation
│   └── management/            # Management commands
├── sc/                         # System scripts
│   ├── cleanup_snapshots.sh
│   ├── cleanup_stuck_deployments.sh
│   └── run_scheduler.sh
├── scheduler/                  # Task scheduler
│   ├── models.py              # ScheduledTask model
│   ├── views.py               # Task management
│   └── management/commands/   # Scheduler daemon
├── scripts/                    # Script management app
├── settings/                   # Global settings
│   ├── models.py              # Credentials, vCenter, Variables
│   └── views.py               # Settings management
├── snapshots/                  # Snapshot management
├── templates/                  # HTML templates
│   ├── base/                  # Base templates
│   ├── deploy/                # Deployment forms
│   ├── inventory/             # Inventory views
│   ├── playbooks/             # Playbook views
│   ├── scheduler/             # Scheduler views
│   └── ...
├── users/                      # User management
├── diaken/                     # Django project settings
│   ├── settings.py            # Main settings
│   └── urls.py                # URL routing
├── manage.py                   # Django management
├── requirements.txt            # Python dependencies
└── db.sqlite3                  # Database (development)
```

## 🔐 Security Best Practices

### SSH Keys
- Keys stored with 0600 permissions
- Automatic permission validation
- Format validation (RSA, ED25519)
- Secure storage in media/ssh/

### Credentials
- Passwords encrypted in database
- vCenter credentials secured
- Windows credentials protected
- No hardcoded credentials

### Network Security
- StrictHostKeyChecking=no only for automation
- WinRM over HTTPS recommended
- Firewall rules for Ansible
- VPN access recommended

### Application Security
- User authentication required
- CSRF protection enabled
- SQL injection prevention
- XSS protection
- Input validation on all forms

## 📊 Monitoring & Logging

### Dashboard Metrics
- Total VMs deployed
- Success/failure rates
- Active hosts count
- Recent deployments
- System health status

### Deployment History
- Complete audit trail
- Ansible output logs
- Execution timestamps
- User tracking
- Error messages

### Log Files
```bash
# Ansible logs
/var/log/ansible/

# Deployment logs
/opt/www/app/logs/deployments/

# Scheduler logs
/opt/www/app/logs/scheduler/

# Django logs
/opt/www/app/logs/django/
```

## 🐛 Troubleshooting

### Common Issues

#### Error: "Hostname already exists"
**Cause**: Hostname is already registered in inventory  
**Solution**: Use a different hostname or delete the existing host

#### Error: "VM already exists in vCenter"
**Cause**: VM with that name exists in vCenter  
**Solution**: Use a different name or delete the existing VM

#### Error: "Connection refused" (Linux)
**Cause**: SSH not accessible or firewall blocking  
**Solution**: 
- Verify SSH is running: `systemctl status sshd`
- Check firewall: `firewall-cmd --list-all`
- Test connection: `ssh user@host`

#### Error: "Connection reset by peer" (Windows)
**Cause**: WinRM not configured or listener issue  
**Solution**:
- Verify WinRM: `winrm get winrm/config`
- Check listener: `winrm enumerate winrm/config/Listener`
- Ensure listener on Address=* (not specific IP)

#### Error: "recursive loop detected"
**Cause**: Playbook using incorrect variable  
**Solution**: Use `inventory_hostname` instead of `target_host`

#### Error: "YAML syntax error"
**Cause**: Invalid YAML in playbook  
**Solution**: Check indentation (use spaces, not tabs)

### Cleanup Stuck Deployments
```bash
cd /opt/www/app
python manage.py shell

from history.models import DeploymentHistory
DeploymentHistory.objects.filter(status='in_progress').update(status='failed')
```

Or use the web interface:
**History → Cleanup Stuck Deployments**

### Reset Scheduler
```bash
cd /opt/www/app/sc
./run_scheduler.sh restart
```

## 🔄 Maintenance

### Backup Database
```bash
# SQLite
cp /opt/www/app/db.sqlite3 /backup/db.sqlite3.$(date +%Y%m%d)

# PostgreSQL
pg_dump diaken > /backup/diaken_$(date +%Y%m%d).sql
```

### Cleanup Old Logs
```bash
# Remove logs older than 30 days
find /var/log/ansible/ -type f -mtime +30 -delete
find /opt/www/app/logs/ -type f -mtime +30 -delete
```

### Update Dependencies
```bash
cd /opt/www/app
source venv/bin/activate
pip install --upgrade -r requirements.txt
python manage.py migrate
```

### Cleanup Old Snapshots
```bash
cd /opt/www/app/sc
./cleanup_snapshots.sh
```

## 📚 Documentation

Comprehensive documentation available in the `docs/` directory:

- **[PLAYBOOK_MANAGEMENT_SYSTEM.md](docs/PLAYBOOK_MANAGEMENT_SYSTEM.md)** - Complete playbook management guide
- **[SCHEDULER_README.md](docs/SCHEDULER_README.md)** - Task scheduler documentation
- **[USER_MANAGEMENT_GUIDE.md](docs/USER_MANAGEMENT_GUIDE.md)** - User and permissions guide
- **[WINDOWS_WINRM_IP_FIX.md](docs/WINDOWS_WINRM_IP_FIX.md)** - Windows WinRM configuration
- **[DEPLOYMENT_CLEANUP_README.md](docs/DEPLOYMENT_CLEANUP_README.md)** - Cleanup procedures
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history and changes

## 🚀 Production Deployment

### Using Gunicorn + Nginx

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Create systemd service:
```bash
sudo vim /etc/systemd/system/diaken.service
```

```ini
[Unit]
Description=Diaken Django Application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/www/app
Environment="PATH=/opt/www/app/venv/bin"
ExecStart=/opt/www/app/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8001 diaken.wsgi:application

[Install]
WantedBy=multi-user.target
```

3. Configure Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /opt/www/app/static/;
    }

    location /media/ {
        alias /opt/www/app/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. Start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable diaken
sudo systemctl start diaken
sudo systemctl restart nginx
```

## 🤝 Contributing

This is a proprietary system. For feature requests or bug reports, contact the development team.

## 📝 License

**Proprietary** - All rights reserved

Unauthorized copying, modification, distribution, or use of this software is strictly prohibited.

## 👥 Authors & Credits

**Development Team**:
- Infrastructure Automation Team
- DevOps Engineering

**Contact**: 
- Email: support@example.com
- Repository: https://github.com/htheran/diakendev

## 🎯 Roadmap

### Planned Features
- [ ] Multi-tenancy support
- [ ] RBAC (Role-Based Access Control)
- [ ] API REST interface
- [ ] Terraform integration
- [ ] Kubernetes deployment support
- [ ] Advanced reporting and analytics
- [ ] Mobile app for monitoring
- [ ] Integration with monitoring tools (Prometheus, Grafana)
- [ ] Backup and disaster recovery automation
- [ ] Cost tracking and optimization

## ⚙️ Configuration

### Environment Variables (.env file)

**Required before running the application:**

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

**Required variables:**

```bash
# Django Security
DJANGO_SECRET_KEY=<generate-with-command-below>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-server.example.com,10.100.x.x,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-server.example.com

# Credential Encryption
ENCRYPTION_KEY=<generate-with-command-below>

# Database (Optional - defaults to SQLite)
DB_ENGINE=sqlite3
DB_NAME=db.sqlite3

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

### Generate Security Keys

```bash
# Generate SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Generate ENCRYPTION_KEY
python security_fixes/credential_encryption.py generate-key
```

### Database Migration

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Migrate Existing Credentials (if any)

If you have existing credentials in the database:

```bash
python security_fixes/migrate_credentials.py
```

## 🚀 Production Deployment

### Quick Start (Oracle Linux 9.6)

**Automated deployment in 10-15 minutes:**

```bash
# 1. Clone repository
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO

# 2. Edit configuration
nano deploy_production.sh
# Change: GITHUB_REPO, SERVER_NAME, SERVER_IP

# 3. Run automated script
sudo bash deploy_production.sh

# 4. Create superuser
sudo -u apache /opt/www/diaken/venv/bin/python /opt/www/diaken/manage.py createsuperuser --settings=diaken.settings_production

# 5. Access application
# http://your-server.example.com/
```

### Documentation

- **Quick Start Guide**: [`QUICK_START_PRODUCCION.md`](QUICK_START_PRODUCCION.md)
- **Complete Deployment Guide**: [`DEPLOYMENT_PRODUCCION.md`](DEPLOYMENT_PRODUCCION.md)
- **Network/IP Automation Solution**: [`SOLUCION_CAMBIO_RED_IP.md`](SOLUCION_CAMBIO_RED_IP.md)

### Architecture

```
Internet/Intranet → Apache httpd (80/443) → mod_wsgi → Django → SQLite/PostgreSQL
```

### Key Technologies

- **Web Server**: Apache httpd + mod_wsgi
- **Framework**: Django 5.2.6
- **Python**: 3.9+
- **OS**: Oracle Linux 9.6 (RHEL compatible)
- **VMware CLI**: govc (for network changes)
- **Automation**: Ansible 2.14+

### Network Automation Features

**Solved Problem**: Automatic network change from DVS to Standard with DirectPath I/O enabled

- ✅ Uses **govc CLI** instead of pyVmomi (more reliable)
- ✅ Supports DVS → Standard, Standard → DVS, DVS → DVS
- ✅ Works with DirectPath I/O enabled NICs
- ✅ No manual intervention required
- ✅ Automatic reboot and verification

**Deployment Flow**:
```
1. Clone VM from template (pyVmomi)
2. Boot VM and verify SSH
3. Run Ansible playbook:
   - Schedule reboot (shutdown -r +1)
   - Change hostname
   - Configure IP with nmcli
4. Change network in vCenter (govc)
5. Wait for reboot (90s)
6. Verify SSH on new IP
7. ✅ Deployment complete
```

## 📞 Support

For support, issues, or feature requests:
1. Check the documentation in `docs/`
2. Review troubleshooting section
3. Contact the development team
4. Submit an issue on GitHub (if applicable)

---

**Version**: 2.0.0  
**Last Updated**: October 15, 2025  
**Django Version**: 5.2.6  
**Python Version**: 3.12  
**Status**: Production Ready ✅
