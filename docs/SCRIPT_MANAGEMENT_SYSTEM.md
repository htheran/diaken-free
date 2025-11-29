# Script Management System

## Overview

The Script Management System provides a comprehensive solution for managing and organizing Bash scripts (for RedHat/Debian Linux) and PowerShell scripts (for Windows) within the Diaken infrastructure automation platform.

## Features

### ✅ Core Functionality

- **Create Scripts**: Write scripts directly in the web interface with syntax highlighting
- **Upload Scripts**: Upload existing script files (.sh or .ps1)
- **Edit Scripts**: Modify script content and metadata
- **View Scripts**: Display script details and content with copy-to-clipboard functionality
- **Download Scripts**: Download scripts for local use or backup
- **Delete Scripts**: Remove scripts with confirmation (deletes both DB record and file)
- **Toggle Active/Inactive**: Enable or disable scripts without deletion

### 🎯 Organization

Scripts are organized by three dimensions:

1. **OS Family**:
   - `redhat` - RedHat, CentOS, Oracle Linux
   - `debian` - Debian, Ubuntu
   - `windows` - Windows Server/Desktop

2. **Target Type**:
   - `host` - Execute on a single host
   - `group` - Execute on a group of hosts

3. **Status**:
   - `active` - Available for execution
   - `inactive` - Hidden from execution but preserved

### 📁 File Structure

Scripts are stored in organized directories:

```
/opt/www/app/media/scripts/
├── redhat/
│   ├── host/
│   │   └── script_name.sh
│   └── group/
│       └── script_name.sh
├── debian/
│   ├── host/
│   │   └── script_name.sh
│   └── group/
│       └── script_name.sh
└── powershell/
    ├── host/
    │   └── script_name.ps1
    └── group/
        └── script_name.ps1
```

## Database Model

### Script Model

```python
class Script(models.Model):
    name = CharField(max_length=255)           # Script name (without extension)
    description = TextField(blank=True)        # What the script does
    target_type = CharField(choices=['host', 'group'])
    os_family = CharField(choices=['redhat', 'debian', 'windows'])
    file_path = CharField(max_length=500)      # Auto-generated full path
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**Unique Constraint**: `(name, target_type, os_family)` - prevents duplicate scripts

## URLs and Views

### Available Endpoints

| URL | View | Description |
|-----|------|-------------|
| `/scripts/` | `script_list` | List all scripts grouped by OS and target type |
| `/scripts/create/` | `script_create` | Create new script with inline editor |
| `/scripts/upload/` | `script_upload` | Upload script file from disk |
| `/scripts/<id>/view/` | `script_view` | View script details and content |
| `/scripts/<id>/edit/` | `script_edit` | Edit script content and metadata |
| `/scripts/<id>/download/` | `script_download` | Download script file |
| `/scripts/<id>/delete/` | `script_delete` | Delete script (with confirmation) |
| `/scripts/<id>/toggle-active/` | `script_toggle_active` | Toggle active status (AJAX) |
| `/scripts/get-scripts/` | `get_scripts_ajax` | Get filtered scripts (AJAX) |

## Usage Examples

### 1. Create a New Script

**Via Web Interface:**
1. Navigate to **Scripts → Create Script**
2. Fill in the form:
   - **Name**: `disk_cleanup` (without extension)
   - **Description**: `Clean up temporary files and logs`
   - **Target Type**: `host`
   - **OS Family**: `redhat`
   - **Script Content**: Paste or write your Bash script
3. Click **Save Script**

**Result**: 
- File created: `/opt/www/app/media/scripts/redhat/host/disk_cleanup.sh`
- Permissions: `755` (executable)
- Database record created with metadata

### 2. Upload an Existing Script

**Via Web Interface:**
1. Navigate to **Scripts → Upload Script**
2. Fill in the form:
   - **Name**: `backup_database`
   - **Description**: `Backup PostgreSQL database`
   - **Target Type**: `host`
   - **OS Family**: `debian`
   - **Script File**: Select `backup_database.sh` from your computer
3. Click **Upload Script**

**Result**:
- File uploaded to: `/opt/www/app/media/scripts/debian/host/backup_database.sh`
- Permissions: `755` (executable for Linux)
- Database record created

### 3. Edit a Script

1. Navigate to **Scripts → List Scripts**
2. Find your script and click **Edit** (pencil icon)
3. Modify the script content or metadata
4. Click **Save Script**

**Result**: File is overwritten with new content, metadata updated

### 4. View Script Details

1. Navigate to **Scripts → List Scripts**
2. Click **View** (eye icon) on any script
3. See:
   - Full metadata (name, type, OS, status, timestamps)
   - Complete script content with syntax highlighting
   - Copy-to-clipboard button
   - Action buttons (Edit, Download, Delete)

### 5. Download a Script

1. From the script list or detail view, click **Download**
2. Browser downloads the file with correct extension

**Use Cases**:
- Backup scripts locally
- Share scripts with team members
- Use scripts outside the platform

### 6. Delete a Script

1. Click **Delete** (trash icon) on any script
2. Confirm deletion in the modal dialog
3. Script is removed from both database and filesystem

**Warning**: This action cannot be undone!

## Example Scripts Included

The system comes with 3 example scripts:

### 1. system_info.sh (RedHat)
- **Target**: Host
- **OS**: RedHat/CentOS/Oracle Linux
- **Purpose**: Collect comprehensive system information
- **Includes**: OS details, kernel, uptime, CPU, memory, disk, network, services, packages

### 2. system_info.sh (Debian)
- **Target**: Host
- **OS**: Debian/Ubuntu
- **Purpose**: Collect comprehensive system information
- **Includes**: OS details, kernel, uptime, CPU, memory, disk, network, services, APT packages

### 3. system_info.ps1 (Windows)
- **Target**: Host
- **OS**: Windows
- **Purpose**: Collect comprehensive system information
- **Includes**: OS details, computer system, CPU, memory, disk, network adapters, IP config, services, hotfixes

## Management Commands

### Import Example Scripts

```bash
python manage.py import_example_scripts
```

**Purpose**: Import the 3 example scripts into the database

**Output**:
```
✓ Imported: system_info (RedHat/CentOS/Oracle Linux/Host)
✓ Imported: system_info (Debian/Ubuntu/Host)
✓ Imported: system_info (Windows/Host)

============================================================
Import Summary:
============================================================
Imported: 3
Skipped: 0
Total: 3
```

## File Validation

### Automatic Validation

The system automatically validates:

1. **File Extensions**:
   - RedHat/Debian scripts must end with `.sh`
   - Windows scripts must end with `.ps1`

2. **Script Names**:
   - Cannot contain: `/ \ : * ? " < > |`
   - Extensions are automatically added

3. **Uniqueness**:
   - Same name + target type + OS family = duplicate (rejected)

4. **File Permissions**:
   - Linux scripts: `755` (executable)
   - Windows scripts: `644` (readable)

## Integration with Existing Systems

### Consistency with Playbooks

The script management system follows the same patterns as the playbook system:

| Feature | Playbooks | Scripts |
|---------|-----------|---------|
| Target Types | host, group | host, group |
| OS Families | linux, windows | redhat, debian, windows |
| File Organization | By OS and target | By OS and target |
| Active/Inactive | ✅ | ✅ |
| Upload/Create | ✅ | ✅ |
| Edit/Delete | ✅ | ✅ |
| AJAX Filtering | ✅ | ✅ |

### Menu Structure

```
Sidebar Menu
├── Playbooks
│   ├── List Playbooks
│   └── Upload Playbook
└── Scripts
    ├── List Scripts
    ├── Create Script
    └── Upload Script
```

## Security Considerations

### File System Security

1. **Directory Permissions**: Scripts stored in `/opt/www/app/media/scripts/` with appropriate permissions
2. **Executable Permissions**: Linux scripts automatically set to `755`
3. **User Context**: Scripts execute with the permissions of the Ansible user

### Input Validation

1. **Script Names**: Validated to prevent directory traversal
2. **File Extensions**: Enforced based on OS family
3. **Content Validation**: No automatic execution of uploaded scripts

### Access Control

1. **Login Required**: All views require authentication (`@login_required`)
2. **Django CSRF**: All forms protected with CSRF tokens
3. **Confirmation Dialogs**: Destructive actions require confirmation

## Future Enhancements

### Planned Features

1. **Script Execution**:
   - Execute scripts on hosts/groups directly from the UI
   - Similar to playbook execution
   - Real-time output streaming
   - Execution history

2. **Script Scheduling**:
   - Schedule scripts to run at specific times
   - Recurring execution (cron-like)
   - Integration with existing scheduler

3. **Version Control**:
   - Track script changes over time
   - Rollback to previous versions
   - Diff view between versions

4. **Script Templates**:
   - Pre-built script templates
   - Parameterized scripts
   - Variable substitution

5. **Syntax Highlighting**:
   - Code editor with syntax highlighting
   - Auto-completion
   - Linting and validation

6. **Script Categories**:
   - Tag scripts by category (backup, monitoring, cleanup, etc.)
   - Filter by category
   - Search functionality

7. **Execution Logs**:
   - Store execution results
   - Success/failure tracking
   - Output capture and display

## Troubleshooting

### Common Issues

#### 1. Script Not Appearing in List

**Cause**: Script marked as inactive or wrong OS family/target type

**Solution**:
- Check the script's active status
- Verify OS family and target type match your filter
- Check database: `python manage.py shell` → `from scripts.models import Script; Script.objects.all()`

#### 2. File Not Found Error

**Cause**: Database record exists but file is missing

**Solution**:
```bash
# Find orphaned records
python manage.py shell
from scripts.models import Script
import os
for s in Script.objects.all():
    if not os.path.exists(s.file_path):
        print(f"Missing: {s.name} - {s.file_path}")
```

#### 3. Permission Denied

**Cause**: Script file doesn't have execute permissions

**Solution**:
```bash
chmod +x /opt/www/app/media/scripts/redhat/host/script_name.sh
```

#### 4. Upload Fails with Extension Error

**Cause**: File extension doesn't match OS family

**Solution**:
- RedHat/Debian: Use `.sh` extension
- Windows: Use `.ps1` extension

## Technical Details

### Model Methods

```python
script.get_extension()          # Returns '.sh' or '.ps1'
script.get_full_filename()      # Returns 'script_name.sh'
script.get_directory_path()     # Returns '/opt/www/app/media/scripts/redhat/host'
script.get_full_path()          # Returns full file path
```

### Form Processing

**ScriptForm**: Create/edit with inline content
- Reads existing file content for editing
- Writes content to file on save
- Sets executable permissions for Linux

**ScriptUploadForm**: Upload existing file
- Validates file extension
- Writes uploaded file to correct location
- Sets appropriate permissions

### AJAX Endpoints

**get_scripts_ajax**: Filter scripts dynamically
```javascript
fetch('/scripts/get-scripts/?target_type=host&os_family=redhat')
  .then(response => response.json())
  .then(data => {
    // data.scripts = [{id, name, description, filename}, ...]
  });
```

## Files Created

### Application Files
- `scripts/__init__.py` - App initialization
- `scripts/apps.py` - App configuration
- `scripts/models.py` - Script model
- `scripts/admin.py` - Django admin configuration
- `scripts/forms.py` - ScriptForm and ScriptUploadForm
- `scripts/views.py` - All view functions
- `scripts/urls.py` - URL routing
- `scripts/migrations/0001_initial.py` - Database migration

### Management Commands
- `scripts/management/commands/import_example_scripts.py`

### Templates
- `templates/scripts/script_list.html` - List view
- `templates/scripts/script_form.html` - Create/edit form
- `templates/scripts/script_upload_form.html` - Upload form
- `templates/scripts/script_view.html` - Detail view
- `templates/scripts/script_confirm_delete.html` - Delete confirmation

### Example Scripts
- `media/scripts/redhat/host/system_info.sh`
- `media/scripts/debian/host/system_info.sh`
- `media/scripts/powershell/host/system_info.ps1`

### Configuration
- Updated `diaken/settings.py` - Added 'scripts' to INSTALLED_APPS
- Updated `diaken/urls.py` - Added scripts URL pattern
- Updated `templates/base/sidebar.html` - Added Scripts menu

## Summary

The Script Management System provides a complete solution for organizing and managing automation scripts across multiple operating systems and deployment targets. It maintains consistency with the existing playbook system while adding powerful features for script lifecycle management.

**Key Benefits**:
- ✅ Centralized script repository
- ✅ Organized by OS and target type
- ✅ Web-based management (no SSH required)
- ✅ Version tracking through database
- ✅ Easy sharing and backup
- ✅ Consistent with existing infrastructure
- ✅ Ready for future execution integration

**Next Steps**:
1. Test the system by creating/uploading scripts
2. Integrate with deployment execution (future)
3. Add scheduling capabilities (future)
4. Implement version control (future)
