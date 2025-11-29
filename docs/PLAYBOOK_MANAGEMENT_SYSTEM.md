# Playbook Management System - Complete Documentation

## Overview
Complete playbook management system with inline YAML editing, file upload, and comprehensive CRUD operations for Ansible playbooks.

## Features Implemented

### Core Functionality
- **Create Playbooks**: Write playbooks directly in web interface with YAML editor
- **Upload Playbooks**: Upload existing .yml or .yaml files
- **Edit Playbooks**: Modify playbook content and metadata with inline editing
- **View Playbooks**: Display playbook details with syntax-highlighted content
- **Download Playbooks**: Download playbooks for backup or local use
- **Delete Playbooks**: Remove playbooks with confirmation (deletes both DB record and file)

### Organization Structure
Playbooks organized by 2 dimensions:
1. **OS Family**: redhat, debian, windows
2. **Target Type**: host (individual hosts), group (groups of hosts)

### File Structure
```
/opt/www/app/media/playbooks/
├── host/          # Playbooks for individual hosts
└── group/         # Playbooks for groups of hosts
```

## Database Model

### Playbook Model
```python
class Playbook(models.Model):
    name = CharField(max_length=255)                    # Playbook name (without .yml)
    description = TextField(blank=True, null=True)      # Optional description
    playbook_type = CharField(choices=['host', 'group']) # Target type
    os_family = CharField(choices=['redhat', 'debian', 'windows'])
    file = FileField(upload_to='playbooks/{playbook_type}/')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### Model Methods
- `__str__()` - Returns playbook name
- File automatically saved to correct directory based on playbook_type

## URLs and Views

### Available Endpoints
| URL | View | Description |
|-----|------|-------------|
| `/playbooks/` | playbook_list | List all playbooks grouped by OS family and type |
| `/playbooks/create/` | playbook_create | Create new playbook with inline YAML editor |
| `/playbooks/upload/` | playbook_upload | Upload playbook file (.yml/.yaml) |
| `/playbooks/<id>/view/` | playbook_view | View playbook details and content |
| `/playbooks/<id>/edit/` | playbook_edit | Edit playbook with inline YAML editor |
| `/playbooks/<id>/download/` | playbook_download | Download playbook file |
| `/playbooks/<id>/delete/` | playbook_delete | Delete playbook (with confirmation) |
| `/playbooks/host/` | playbook_list_host | Filter host playbooks only |
| `/playbooks/group/` | playbook_list_group | Filter group playbooks only |

## Forms

### PlaybookContentForm (Create/Edit)
**Purpose**: Create or edit playbooks with inline YAML content editing

**Fields**:
- `name` - Playbook name (without .yml extension)
- `description` - Optional description
- `playbook_type` - Host or Group
- `os_family` - RedHat, Debian, or Windows
- `playbook_content` - YAML content (20-row textarea with monospace font)

**Features**:
- Reads existing file content when editing
- Validates YAML syntax using PyYAML
- Auto-removes .yml/.yaml extensions from name if user adds them
- Writes content to file on save
- Auto-generates filename: `{name}.yml`

**Validation**:
- Required fields: name, playbook_type, os_family, playbook_content
- YAML syntax validation (raises error if invalid)
- Name sanitization (removes extensions)

### PlaybookForm (Upload)
**Purpose**: Upload existing playbook files

**Fields**:
- `name` - Playbook name
- `description` - Optional description
- `playbook_type` - Host or Group
- `os_family` - RedHat, Debian, or Windows
- `file` - File upload (.yml or .yaml only)

**Features**:
- File extension validation (.yml, .yaml)
- Saves uploaded file to correct directory

## Templates

### 1. playbook_list.html
**Purpose**: List all playbooks grouped by OS family and target type

**Features**:
- Groups playbooks by OS family (RedHat, Debian, Windows)
- Shows host and group playbooks side-by-side
- Color-coded headers by OS family:
  - RedHat: Red (bg-danger)
  - Debian: Yellow (bg-warning)
  - Windows: Blue (bg-primary)
- Action buttons per playbook:
  - View (info)
  - Edit (warning)
  - Download (success)
  - Delete (danger with modal confirmation)
- Top buttons:
  - Create Playbook (primary)
  - Upload Playbook (success)
- Empty state message with links to create/upload

**Layout**:
```
┌─────────────────────────────────────────┐
│ Playbooks      [Create] [Upload]        │
├─────────────────────────────────────────┤
│ RedHat Playbooks                        │
│ ┌──────────────┬──────────────┐        │
│ │ Host (3)     │ Group (2)    │        │
│ │ - Playbook1  │ - Playbook4  │        │
│ │ - Playbook2  │ - Playbook5  │        │
│ │ - Playbook3  │              │        │
│ └──────────────┴──────────────┘        │
├─────────────────────────────────────────┤
│ Debian Playbooks                        │
│ ...                                     │
└─────────────────────────────────────────┘
```

### 2. playbook_form.html
**Purpose**: Create or edit playbook with inline YAML editor

**Features**:
- Dynamic title: "Create Playbook" or "Edit Playbook"
- Form fields in organized layout:
  - Row 1: Name (50%), Type (25%), OS Family (25%)
  - Row 2: Description (100%)
  - Row 3: YAML Content (100%, 20 rows, monospace)
- Error display for each field
- Help text for each field
- Cancel and Save buttons
- Monospace font for YAML editor

### 3. playbook_upload.html
**Purpose**: Upload existing playbook file

**Features**:
- Info alert explaining difference between upload and create
- File input with .yml/.yaml filter
- Auto-fills name from filename (without extension)
- File preview showing:
  - Selected filename
  - File size (formatted: KB, MB)
- Same metadata fields as create form
- Cancel and Upload buttons

### 4. playbook_view.html
**Purpose**: View playbook details and content

**Features**:
- Metadata table showing:
  - Name, Filename
  - Description
  - Type (badge: Host=info, Group=success)
  - OS Family (badge: RedHat=danger, Debian=warning, Windows=primary)
  - Created/Updated timestamps
- YAML content display:
  - Syntax-highlighted code block
  - Copy to clipboard button
  - Scrollable (max 600px height)
- Action buttons:
  - Back to List (secondary)
  - Edit (warning)
  - Download (success)
  - Delete (danger with modal)
- Delete confirmation modal

### 5. playbook_delete.html
**Purpose**: Confirm playbook deletion

**Features**:
- Danger-themed header
- Warning alerts about permanent deletion
- Complete playbook details table
- List of what will be deleted:
  - Database record
  - Physical file path
- Large Cancel and Delete buttons
- CSRF protection

## Menu Integration

Added to sidebar menu:
```
Playbooks
├── List Playbooks
├── Create Playbook
└── Upload Playbook
```

## Example Playbook Included

### System-Info-Report.yml
**Location**: `/opt/www/app/media/playbooks/host/System-Info-Report.yml`

**Purpose**: Comprehensive system information gathering

**Features**:
- Displays system information (hostname, OS, kernel, architecture)
- Checks disk usage (df -h)
- Checks memory usage (free -h)
- Lists running services
- Creates report directory (/tmp/system_reports)
- Generates detailed text report
- Saves to /tmp/system_reports/system_info.txt

**Target**: Host (individual hosts)
**OS Family**: RedHat

**Usage**:
```bash
ansible-playbook System-Info-Report.yml -i inventory
```

## Management Commands

### create_example_playbook
```bash
python manage.py create_example_playbook
```
Creates the System-Info-Report example playbook. Skips if already exists.

## YAML Validation

### Automatic Validation
1. **Syntax Check**: Uses PyYAML to validate YAML syntax before saving
2. **Error Messages**: Shows specific YAML errors to user
3. **Prevents Invalid Playbooks**: Won't save if YAML is malformed

### Example Validation Errors:
- Missing colons
- Incorrect indentation
- Invalid YAML structure
- Unclosed quotes/brackets

## Security Features

1. **Login Required**: All views require authentication (`@login_required`)
2. **CSRF Protection**: All forms use CSRF tokens
3. **Input Validation**: 
   - Playbook names validated
   - YAML syntax validated
   - File extensions validated (.yml, .yaml only)
4. **Confirmation Dialogs**: Destructive actions require confirmation
5. **File System Security**: Playbooks stored in controlled directory

## User Experience Features

### Success/Error Messages
- Create: "Playbook '{name}' created successfully!"
- Edit: "Playbook '{name}' updated successfully!"
- Delete: "Playbook '{name}' deleted successfully!"
- Upload: "Playbook '{name}' uploaded successfully!"
- Errors: Specific error messages for validation failures

### Copy to Clipboard
- View page includes copy button for playbook content
- Visual feedback (button changes to "Copied!" for 2 seconds)
- Uses modern Clipboard API

### File Preview
- Upload form shows selected file details
- Auto-fills name from filename
- Shows file size in human-readable format

### Grouped Display
- Playbooks organized by OS family
- Side-by-side host/group display
- Badge counts for each category
- Color-coded by OS family

## Integration with Existing Systems

### Consistency with Scripts
- Same target types (host, group)
- Similar OS family structure
- Same file organization pattern
- Consistent UI/UX
- Same authentication requirements

### Execution Integration
- Playbooks can be executed via:
  - `/deploy/playbook/` (Linux)
  - `/deploy/playbook/windows/` (Windows)
- Playbook selection dropdowns populated from database
- Execution creates logs and reports

## Files Created/Modified

### Application Files (8)
- `playbooks/forms.py` - Added PlaybookContentForm
- `playbooks/views.py` - Added create, view, download views; updated edit, list, delete
- `playbooks/urls.py` - Added create, view, download URLs
- `playbooks/management/__init__.py` - Management commands package
- `playbooks/management/commands/__init__.py` - Commands package
- `playbooks/management/commands/create_example_playbook.py` - Example playbook creator

### Templates (5)
- `templates/playbooks/playbook_list.html` - List view with grouping
- `templates/playbooks/playbook_form.html` - Create/edit form
- `templates/playbooks/playbook_upload.html` - Upload form
- `templates/playbooks/playbook_view.html` - Detail view
- `templates/playbooks/playbook_delete.html` - Delete confirmation

### Configuration Updates (1)
- `templates/base/sidebar.html` - Added "Create Playbook" menu item

### Example Playbooks (1)
- `media/playbooks/host/System-Info-Report.yml` - Example playbook

### Documentation (1)
- `docs/PLAYBOOK_MANAGEMENT_SYSTEM.md` - This file

### Dependencies Added (1)
- `pyyaml==6.0.3` - YAML parsing and validation

## Usage Examples

### Create Playbook
1. Navigate to Playbooks → Create Playbook
2. Fill form:
   - Name: "My-Custom-Playbook" (without .yml)
   - Description: "What this playbook does"
   - Type: Host or Group
   - OS Family: RedHat, Debian, or Windows
3. Paste or write YAML content in textarea
4. Click "Save Playbook"
5. Result: File created at `/opt/www/app/media/playbooks/{type}/My-Custom-Playbook.yml`

### Upload Playbook
1. Navigate to Playbooks → Upload Playbook
2. Click "Choose File" and select .yml or .yaml file
3. Name auto-fills from filename (editable)
4. Fill metadata (description, type, OS family)
5. Click "Upload Playbook"
6. Result: File uploaded to correct location

### Edit Playbook
1. Navigate to Playbooks → List Playbooks
2. Find playbook and click "Edit" button
3. Modify any field (name, description, type, OS, content)
4. Click "Save Playbook"
5. Result: File updated with new content

### View Playbook
1. Navigate to Playbooks → List Playbooks
2. Find playbook and click "View" button
3. See complete details and content
4. Use "Copy to Clipboard" to copy YAML content
5. Use action buttons: Edit, Download, Delete

### Download Playbook
1. From list or view page, click "Download" button
2. Browser downloads file as `{name}.yml`
3. Use for backup or local execution

### Delete Playbook
1. From list or view page, click "Delete" button
2. Review playbook details in confirmation page
3. Click "Yes, Delete Playbook"
4. Result: Database record and file both deleted

## Future Enhancements (Planned)

1. **Syntax Highlighting**: Code editor with YAML syntax highlighting
2. **Version Control**: Track changes, rollback, diff view
3. **Templates**: Pre-built parameterized playbook templates
4. **Validation**: Ansible-lint integration for playbook validation
5. **Execution History**: Track when/where playbooks were executed
6. **Variables**: Manage playbook variables separately
7. **Roles**: Support for Ansible roles
8. **Collections**: Organize playbooks into collections
9. **Sharing**: Export/import playbooks between systems
10. **Scheduling**: Schedule playbooks to run at specific times

## Key Benefits

✅ Centralized playbook repository
✅ Organized by OS and target type
✅ Web-based management (no SSH required)
✅ Inline YAML editing with validation
✅ Easy sharing and backup
✅ Consistent with existing infrastructure
✅ Full CRUD operations
✅ Automatic file management
✅ Copy-to-clipboard functionality
✅ Grouped display for easy navigation

## Technical Notes

- **Django App**: 'playbooks' (already existed)
- **Model**: Playbook with fields for name, description, type, OS, file
- **Forms**: 
  - PlaybookContentForm (inline editor with YAML validation)
  - PlaybookForm (file upload)
- **Views**: All require `@login_required`
- **File Storage**: Django FileField with upload_to pattern
- **YAML Validation**: PyYAML library (yaml.safe_load)
- **File Extension**: Always .yml (auto-added)
- **Permissions**: Standard file permissions (644)

## Troubleshooting

### YAML Validation Errors
**Problem**: "Invalid YAML syntax" error when saving
**Solution**: Check YAML indentation (use spaces, not tabs), ensure proper structure

### File Not Found
**Problem**: "Playbook file not found" when viewing
**Solution**: Check file exists at path shown, verify media directory permissions

### Upload Fails
**Problem**: File upload doesn't work
**Solution**: Check MEDIA_ROOT setting, verify directory permissions (755)

### Can't Edit Content
**Problem**: Edit form doesn't show current content
**Solution**: Verify file exists and is readable, check file permissions

## API Reference

### PlaybookContentForm Methods

#### `__init__(self, *args, **kwargs)`
Initializes form and loads existing playbook content if editing.

#### `clean_name(self)`
Validates and sanitizes playbook name (removes extensions).

#### `clean_playbook_content(self)`
Validates YAML syntax using PyYAML.

#### `save(self, commit=True)`
Saves playbook and writes content to file.

### View Functions

#### `playbook_create(request)`
Handles playbook creation with inline editing.

#### `playbook_edit(request, pk)`
Handles playbook editing with inline editing.

#### `playbook_view(request, pk)`
Displays playbook details and content.

#### `playbook_download(request, pk)`
Returns playbook file as download.

#### `playbook_list(request)`
Lists all playbooks grouped by OS family and type.

#### `playbook_delete(request, pk)`
Handles playbook deletion with confirmation.

## Testing Checklist

- [ ] Create playbook with valid YAML
- [ ] Create playbook with invalid YAML (should show error)
- [ ] Edit existing playbook
- [ ] Upload .yml file
- [ ] Upload .yaml file
- [ ] Upload non-YAML file (should reject)
- [ ] View playbook details
- [ ] Copy playbook content to clipboard
- [ ] Download playbook
- [ ] Delete playbook
- [ ] List playbooks (verify grouping)
- [ ] Navigate between create/upload/list views
- [ ] Test with different OS families
- [ ] Test with host and group types
- [ ] Verify file creation in correct directory
- [ ] Verify file deletion when playbook deleted

## Support

For issues or questions:
1. Check this documentation
2. Review Django logs: `/opt/www/app/logs/`
3. Check playbook files: `/opt/www/app/media/playbooks/`
4. Verify database records: Django admin or shell

## Version History

- **v1.0** (2025-10-15): Initial implementation
  - Create, edit, view, download, delete playbooks
  - Inline YAML editor with validation
  - File upload support
  - Grouped list display
  - Example playbook included
  - Complete documentation

---

**Last Updated**: October 15, 2025
**Author**: Diaken Development Team
**Django Version**: 5.2.6
**Python Version**: 3.12
