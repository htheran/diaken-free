# Changelog - Diaken Automated VM Deployment System

All notable changes to the Diaken project will be documented in this file.

## [2.0.0] - 2025-10-15

### 🎉 Major Features

#### 📦 Complete Playbook Management System
- **Inline YAML Editor**: Create and edit playbooks directly in web interface
- **YAML Syntax Validation**: Real-time validation using PyYAML
- **Full CRUD Operations**: Create, Read, Update, Delete playbooks
- **Organized Storage**: Playbooks organized by OS family (RedHat, Debian, Windows) and type (host, group)
- **Copy-to-Clipboard**: Easy copying of playbook content
- **Download Playbooks**: Download for backup or local use
- **Example Playbooks**: System-Info-Report.yml included
- **5 New Templates**: List, form, view, upload, delete interfaces

#### 📜 Complete Script Management System
- **Bash Script Support**: RedHat and Debian scripts
- **PowerShell Support**: Windows script management
- **Inline Script Editor**: Write scripts directly in browser
- **Upload Scripts**: Upload existing .sh and .ps1 files
- **Full CRUD**: Create, edit, view, download, delete scripts
- **Active/Inactive Toggle**: Enable/disable without deletion
- **Organized by OS**: redhat, debian, windows folders
- **Example Scripts**: system_info scripts for all OS families

#### 📅 Enhanced Task Scheduler
- **Recurring Tasks**: Daily, weekly, monthly schedules
- **One-Time Tasks**: Schedule for specific date/time
- **Playbook Scheduling**: Schedule playbook executions
- **Script Scheduling**: Schedule script executions
- **Email Notifications**: Notify on task completion
- **Execution History**: Complete audit trail
- **OS Family Support**: Linux and Windows tasks
- **Snapshot Integration**: Create snapshots before scheduled tasks

#### 🔔 Microsoft Teams Notifications
- **Webhook Integration**: Connect to Microsoft Teams channels
- **Deployment Notifications**: VM deployment status alerts
- **Playbook Notifications**: Playbook execution results
- **Scheduled Task Notifications**: Task completion alerts
- **Color-Coded Messages**: Green (success), Red (failed), Yellow (running)
- **Failures-Only Mode**: Only notify on failures
- **Test Notifications**: Test webhook before using
- **Notification Logs**: Complete notification history

#### 🖥️ Multi-Hypervisor Support
- **Optional vCenter Field**: vCenter field now optional in host creation
- **Proxmox Support**: Add Proxmox VMs to inventory
- **Standalone VMs**: Manage VMs without hypervisor
- **Other Hypervisors**: Support for any hypervisor
- **Flexible Inventory**: Mixed hypervisor environments

#### 🪟 Windows Management Improvements
- **Native Windows Update**: COM objects approach (no PSWindowsUpdate)
- **EULA Auto-Accept**: Automatically accept update EULAs
- **Driver Updates**: Include driver updates in search
- **Detailed Results**: HResult codes for each update
- **SYSTEM Privileges**: Run updates with SYSTEM account
- **WinRM IP Fix**: Listener configuration for Address=*
- **Scheduled Task Fix**: Windows scheduled tasks now respect schedule time

#### 📸 Snapshot Enhancements
- **Scheduled Task Snapshots**: Snapshots from scheduled tasks saved to database
- **Complete History**: All snapshots (manual and scheduled) in UI
- **Manual Deletion**: Delete any snapshot from web interface
- **Zombie Prevention**: Sync between vCenter and Django database
- **Retention Policies**: Automatic cleanup based on retention

### ✨ Enhancements

#### Performance Optimizations
- **RedHat Playbook Optimization**: 93% output reduction when no updates
- **Conditional Execution**: Skip unnecessary tasks
- **Faster Execution**: Reduced CPU/RAM consumption
- **Better User Experience**: Clear, concise messaging

#### Deployment Improvements
- **Stuck Deployment Cleanup**: Automatic cleanup of stuck deployments
- **6-Hour Timeout**: Increased from 2h to accommodate group updates
- **Cleanup Command**: `python manage.py cleanup_stuck_deployments`
- **Cron Integration**: Automatic cleanup every 30 minutes
- **UI Indicators**: Visual indicators for stuck deployments

#### Documentation
- **Complete Reorganization**: All docs moved to `/docs/` folder
- **English Translation**: Main README translated to English
- **39 Documentation Files**: Comprehensive guides and references
- **INDEX.md**: Complete documentation index
- **Quick Reference**: Common tasks and troubleshooting

### 🔧 Technical Improvements

#### Dependencies
- **PyYAML 6.0.3**: Added for YAML validation
- **Updated Requirements**: All dependencies updated in requirements.txt

#### Code Organization
- **Scripts Folder**: System scripts moved to `/sc/` folder
- **Obsolete Scripts Removed**: 14 test scripts deleted
- **Management Commands**: Added playbook and script import commands
- **Cleaner Root**: Documentation and scripts organized

#### Database Migrations
- **Scheduler Migrations**: New fields for execution_type and os_family
- **Script Model**: Complete script management model
- **Playbook Model**: Enhanced playbook model

### 🐛 Bug Fixes

#### Windows Issues
- **WinRM Listener Fix**: Address=* configuration for dynamic IPs
- **Scheduled Task Fix**: Tasks now execute at scheduled time (not immediately)
- **Update Search Fix**: Include all update types (software AND drivers)
- **EULA Blocking Fix**: Auto-accept EULAs to prevent installation blocks

#### Snapshot Issues
- **Scheduled Snapshot Persistence**: Snapshots from scheduled tasks now saved to database
- **History Visibility**: All snapshots visible in UI
- **Manual Deletion**: Can delete scheduled task snapshots manually

#### Deployment Issues
- **Stuck Deployment Detection**: Automatic detection and cleanup
- **Timeout Handling**: Better timeout management
- **Process Tracking**: Improved process lifecycle management

### 📁 New Files Created

#### Applications
- `playbooks/` - Complete playbook management app (15 files)
- `scripts/` - Complete script management app (15 files)
- `notifications/` - Microsoft Teams notification system (21 files)

#### Templates
- `templates/playbooks/` - 5 playbook management templates
- `templates/scripts/` - 5 script management templates
- `templates/notifications/` - 7 notification templates

#### Documentation
- `docs/INDEX.md` - Complete documentation index
- `docs/PLAYBOOK_MANAGEMENT_SYSTEM.md` - Playbook system guide
- `docs/SCRIPT_MANAGEMENT_SYSTEM.md` - Script system guide
- `docs/NOTIFICATIONS_SYSTEM.md` - Notification system guide
- `docs/WINDOWS_UPDATE_NATIVE_APPROACH.md` - Windows Update guide
- Plus 34 other documentation files

#### Example Files
- `media/playbooks/System-Info-Report.yml` - Example playbook
- `media/playbooks/Update-Windows-Host.yml` - Windows update playbook
- `media/scripts/redhat/host/system_info.sh` - RedHat example
- `media/scripts/debian/host/system_info.sh` - Debian example
- `media/scripts/powershell/host/system_info.ps1` - Windows example

### 🔄 Modified Files

#### Views
- `deploy/views_playbook.py` - Added notification integration
- `deploy/views_playbook_windows.py` - Fixed scheduled task execution
- `scheduler/management/commands/run_scheduled_tasks.py` - Fixed snapshot persistence

#### Forms
- `inventory/forms.py` - Made vCenter field optional
- `playbooks/forms.py` - Added YAML validation
- `scripts/forms.py` - Added script validation

#### Templates
- `templates/inventory/host_form.html` - Updated vCenter field
- `templates/base/sidebar.html` - Added new menu items
- `templates/scheduler/scheduled_tasks_list.html` - Enhanced UI

#### Configuration
- `diaken/settings.py` - Added new apps
- `diaken/urls.py` - Added new URL patterns
- `requirements.txt` - Updated dependencies

### 🗑️ Removed Files

#### Obsolete Scripts (23 files)
- `test_winrm_*.py` - WinRM test scripts
- `test_*_snapshot.py` - Snapshot test scripts
- `diagnose_winrm*.ps1` - WinRM diagnostic scripts
- `verify_winrm_config.ps1` - WinRM verification

#### Moved to /docs/
- All markdown documentation from root
- 15 documentation files reorganized

#### Moved to /sc/
- `cleanup_snapshots.sh`
- `cleanup_stuck_deployments.sh`
- `run_scheduler.sh`
- `run_scheduler_daemon.sh`
- `set_snapshot_retention.sh`

### 📊 Statistics

- **Total Commits**: 10+ commits in this release
- **Files Changed**: 73 files
- **Lines Added**: 4,612+
- **Lines Removed**: 1,741
- **New Features**: 8 major features
- **Bug Fixes**: 6 critical fixes
- **Documentation Files**: 39 files
- **Code Quality**: Improved organization and maintainability

### 🚀 Upgrade Notes

#### Database Migrations
```bash
python manage.py migrate
```

#### Install New Dependencies
```bash
pip install -r requirements.txt
```

#### Import Example Content
```bash
python manage.py create_example_playbook
python manage.py import_example_scripts
```

#### Setup Cron Jobs
```bash
# Cleanup stuck deployments every 30 minutes
*/30 * * * * /opt/www/app/sc/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1

# Run scheduled tasks every minute
* * * * * cd /opt/www/app && /opt/www/app/venv/bin/python manage.py run_scheduled_tasks >> /var/log/scheduler.log 2>&1
```

### ⚠️ Breaking Changes

- **Script Location**: System scripts moved from root to `/sc/` folder
- **Documentation**: All docs moved from root to `/docs/` folder
- **vCenter Field**: Now optional (existing hosts unaffected)

### 🎯 Next Release (Planned)

- [ ] Multi-tenancy support
- [ ] RBAC (Role-Based Access Control)
- [ ] REST API
- [ ] Terraform integration
- [ ] Kubernetes deployment support
- [ ] Advanced reporting and analytics
- [ ] Mobile app for monitoring
- [ ] Prometheus/Grafana integration

---

## [1.0.0] - 2025-09-30

### ✨ Características Principales

#### 🖥️ Gestión de Inventario
- Sistema completo de inventario con Environments, Groups y Hosts
- Interfaz web para gestión de hosts
- Filtrado y búsqueda de hosts
- Organización jerárquica por ambientes y grupos

#### 🚀 Despliegue Automatizado de VMs
- Integración completa con vCenter usando pyVmomi
- Clonado automático de VMs desde templates
- Configuración automática de red (IP, gateway, DNS)
- Configuración automática de hostname
- Post-configuración con Ansible
- Reinicio automático y validación SSH
- Aceptación automática de fingerprint SSH

#### 📜 Gestión de Playbooks
- Sistema de carga y gestión de playbooks Ansible
- Clasificación por tipo (host/group)
- Ejecución de playbooks adicionales post-deploy
- Concatenación de outputs de múltiples playbooks
- Validación y logging completo

#### 📊 Historial de Despliegues
- Registro completo de cada despliegue
- Almacenamiento de outputs de Ansible
- Tracking de duración y timestamps
- Estados: success/failed
- Detalles de VM: hostname, IP, MAC address, datacenter, cluster, template
- Filtrado por estado, tipo y fechas

#### ⚙️ Configuración Global
- Sistema de variables globales organizadas por secciones
- Gestión de credenciales SSH con validación
- Gestión de certificados SSL
- Configuración de vCenter
- Templates Jinja2 para configuraciones

#### 🔧 Ansible Templates (Jinja2)
- Sistema de gestión de templates .j2
- Organización por tipo (host/group)
- Upload y edición desde interfaz web
- Almacenamiento en /opt/www/app/media/j2/

### 🔒 Seguridad y Validaciones
- Validación de duplicados en inventario (hostname e IP)
- Validación de VMs existentes en vCenter
- Gestión segura de llaves SSH (permisos 0600)
- Validación de formato de llaves SSH
- Detección de fallos en playbooks

### 🎨 Interfaz de Usuario
- Dashboard con estadísticas
- Modal de progreso con 8 pasos
- Mensajes de éxito/error claros
- Sidebar con navegación organizada
- Templates Bootstrap responsivos

### 📝 Playbooks Incluidos
- `provision_vm.yml`: Aprovisionamiento básico (hostname + red)
- `Update-Redhat-Host.yml`: Actualización de sistemas RedHat
- `Install-Httpd-Host.yml`: Instalación y configuración de Apache

### 🛠️ Tecnologías
- Django 5.2.6
- Python 3.9+
- pyVmomi (vCenter API)
- Ansible 2.14+
- Bootstrap 4
- FontAwesome
- SQLite

### 📦 Estructura del Proyecto
```
/opt/www/app/
├── diaken/          # Configuración Django
├── deploy/          # App de despliegue
├── inventory/       # App de inventario
├── history/         # App de historial
├── playbooks/       # App de playbooks
├── settings/        # App de configuración
├── login/           # App de autenticación
├── templates/       # Templates HTML
├── static/          # Archivos estáticos
├── media/           # Archivos subidos
│   ├── playbooks/   # Playbooks Ansible
│   ├── j2/          # Templates Jinja2
│   └── ssh/         # Llaves SSH
└── ansible/         # Playbooks de aprovisionamiento
```

### 🔄 Flujo de Despliegue
1. Usuario completa formulario de deploy
2. Validación de duplicados (inventario + vCenter)
3. Conexión a vCenter
4. Clonado de VM desde template
5. Configuración de red
6. Encendido de VM
7. Verificación SSH (IP de plantilla)
8. Ejecución de playbook de aprovisionamiento
9. Reinicio programado
10. Espera y verificación SSH (nueva IP)
11. Aceptación de fingerprint SSH
12. Ejecución de playbook adicional (opcional)
13. Registro en inventario
14. Registro en historial

### 🐛 Correcciones Importantes
- Fix: Variables recursivas en playbooks (target_host → inventory_hostname)
- Fix: Rutas de templates Jinja2 corregidas
- Fix: Detección correcta de fallos en playbooks
- Fix: Concatenación de outputs de múltiples playbooks
- Fix: Almacenamiento correcto de templates en media/j2/
- Fix: Validación de Python interpreter configurable

### 📚 Documentación
- README con instrucciones de instalación
- Variables de entorno documentadas
- Estructura de playbooks documentada
- Ejemplos de uso incluidos
