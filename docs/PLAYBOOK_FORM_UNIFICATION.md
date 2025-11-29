# Playbook Form Unification - Linux & Windows

## Overview

The Linux and Windows playbook execution forms have been unified to provide a consistent, simplified user experience. Both forms now use the same structure and logic.

---

## What Changed

### Before (Redundant Forms):

```
❌ /deploy/playbook/          → Execute on Linux Host
❌ /deploy/group/              → Execute on Linux Group  
❌ /deploy/playbook/windows/   → Execute on Windows Host
```

**Problems:**
- 3 separate forms for similar functionality
- Inconsistent UX between Linux and Windows
- Confusing navigation
- Duplicate code and logic
- Hard to maintain

### After (Unified Forms):

```
✅ /deploy/playbook/          → Execute on Linux (Host OR Group)
✅ /deploy/playbook/windows/   → Execute on Windows (Host OR Group)
```

**Benefits:**
- Single form per OS with target type selector
- Consistent UX across all platforms
- Cleaner navigation
- Reduced code duplication
- Easier to maintain

---

## Form Structure

Both Linux and Windows forms now follow this structure:

```
┌─────────────────────────────────────────────┐
│ 1. Target Type* [Host / Group]             │
├─────────────────────────────────────────────┤
│ 2. Environment (filter)                     │
├─────────────────────────────────────────────┤
│ 3. Group Filter (shown for host selection) │
├─────────────────────────────────────────────┤
│ 4a. Host* (if target = host)               │
│     OR                                      │
│ 4b. Group* (if target = group)             │
├─────────────────────────────────────────────┤
│ 5. Playbook* (loaded dynamically)          │
├─────────────────────────────────────────────┤
│ 6. ☐ Create snapshot (hosts only)          │
├─────────────────────────────────────────────┤
│ 7. ☐ Schedule for later execution          │
├─────────────────────────────────────────────┤
│ 8. Scheduled Time (if scheduled)           │
├─────────────────────────────────────────────┤
│ [Execute Playbook] [Back]                  │
└─────────────────────────────────────────────┘
```

---

## Features

### 1. Target Type Selection

**Host Execution:**
- Select individual host
- Filter by environment and group
- Create snapshot before execution (optional)
- Schedule execution (optional)
- Loads only HOST playbooks dynamically

**Group Execution:**
- Select entire group
- Execute on all active hosts in group
- No snapshot option (group-wide execution)
- Schedule execution (optional)
- Loads only GROUP playbooks dynamically

### 2. Dynamic Playbook Loading

Playbooks are loaded via AJAX based on:
- **Target Type:** host or group
- **OS Family:** linux or windows

**Endpoint:** `/deploy/playbook/get-playbooks/`

**Request:**
```javascript
{
  target_type: 'host',  // or 'group'
  os_family: 'linux'    // or 'windows'
}
```

**Response:**
```json
{
  "playbooks": [
    {
      "id": 1,
      "name": "Update-Linux-Host",
      "description": "Update packages on Linux host"
    }
  ]
}
```

### 3. Snapshot Support

**For Hosts:**
- Checkbox visible
- Creates vCenter snapshot before execution
- Auto-deleted after retention period
- Requires vCenter credentials

**For Groups:**
- Checkbox hidden
- No snapshot creation
- Group-wide execution doesn't support snapshots

### 4. Scheduled Execution

**Both hosts and groups:**
- Checkbox to enable scheduling
- Datetime picker for execution time
- Immediate execution if not scheduled
- Future enhancement: background task queue

### 5. Smart Filtering

**Environment Filter:**
- Filters both groups and hosts
- Optional (shows all if empty)

**Group Filter:**
- Only shown for host selection
- Filters hosts by group
- Optional (shows all if empty)

---

## Technical Implementation

### Linux Form

**Template:** `/opt/www/app/templates/deploy/deploy_playbook_form.html`

**Views:** `/opt/www/app/deploy/views_playbook.py`

**Functions:**
- `deploy_playbook()` - Render form with Linux hosts
- `execute_playbook()` - Execute on host or group
- `get_playbooks()` - AJAX endpoint for dynamic loading

**Key Changes:**
```python
# Filter only Linux hosts
hosts = Host.objects.filter(active=True, operating_system='linux')

# Handle target type
target_type = request.POST.get('target_type')  # 'host' or 'group'

if target_type == 'host':
    host = Host.objects.get(pk=host_id)
    # Execute on single host
elif target_type == 'group':
    group = Group.objects.get(pk=group_id)
    hosts_in_group = Host.objects.filter(group=group, active=True, operating_system='linux')
    # Execute on all hosts in group
```

### Windows Form

**Template:** `/opt/www/app/templates/deploy/deploy_playbook_windows_form.html`

**Views:** `/opt/www/app/deploy/views_playbook_windows.py`

**Functions:**
- `deploy_playbook_windows()` - Render form with Windows hosts
- `execute_playbook_windows()` - Execute on host or group
- `get_playbooks_windows()` - AJAX endpoint for dynamic loading

**Same structure as Linux, but filters Windows hosts:**
```python
hosts = Host.objects.filter(active=True, operating_system='windows')
```

---

## JavaScript Logic

Both forms use identical JavaScript:

```javascript
// Toggle fields based on target type
$('#target_type').change(function() {
  var targetType = $(this).val();
  
  if (targetType === 'host') {
    $('#host-selection-div').show();
    $('#group-selection-div').hide();
    $('#snapshot-div').show();
    updatePlaybooks();
  } else if (targetType === 'group') {
    $('#host-selection-div').hide();
    $('#group-selection-div').show();
    $('#snapshot-div').hide();
    updatePlaybooks();
  }
});

// Load playbooks dynamically
function updatePlaybooks() {
  var targetType = $('#target_type').val();
  var osFamily = 'linux'; // or 'windows'
  
  $.ajax({
    url: '/deploy/playbook/get-playbooks/',
    data: { target_type: targetType, os_family: osFamily },
    success: function(response) {
      $('#playbook').html('<option value="">Select...</option>');
      response.playbooks.forEach(function(pb) {
        $('#playbook').append('<option value="' + pb.id + '">' + pb.name + '</option>');
      });
    }
  });
}
```

---

## URL Structure

### Linux:
```python
path('playbook/', views.deploy_playbook, name='deploy_playbook'),
path('playbook/execute/', views.execute_playbook, name='execute_playbook'),
path('playbook/get-playbooks/', views.get_playbooks, name='get_playbooks'),
```

### Windows:
```python
path('playbook/windows/', views_playbook_windows.deploy_playbook_windows, name='deploy_playbook_windows'),
path('playbook/windows/execute/', views_playbook_windows.execute_playbook_windows, name='execute_playbook_windows'),
path('playbook/windows/get-playbooks/', views_playbook_windows.get_playbooks_windows, name='get_playbooks_windows'),
```

### Removed (Redundant):
```python
# ❌ No longer needed - integrated in unified form
# path('group/', views_group.execute_group_playbook, name='execute_group_playbook'),
# path('group/execute/', views_group.execute_group_playbook_run, name='execute_group_playbook_run'),
```

---

## Navigation Updates

### Sidebar Menu

**Before:**
```
Deploy
├── Deploy VM (Linux)
├── Deploy VM (Windows)
├── Execute Playbook (Linux)
├── Execute Playbook (Windows)
└── Execute on Group              ← REMOVED
```

**After:**
```
Deploy
├── Deploy VM (Linux)
├── Deploy VM (Windows)
├── Execute Playbook (Linux)      ← Now includes host/group
└── Execute Playbook (Windows)    ← Now includes host/group
```

---

## Playbook Requirements

For the dynamic loading to work correctly, playbooks must have:

1. **playbook_type** field:
   - `'host'` - For single host execution
   - `'group'` - For group execution

2. **os_family** field:
   - `'linux'` - For Linux hosts
   - `'windows'` - For Windows hosts

**Example Playbook Model:**
```python
class Playbook(models.Model):
    PLAYBOOK_TYPE_CHOICES = [
        ('host', 'Host'),
        ('group', 'Group'),
    ]
    
    OS_FAMILY_CHOICES = [
        ('linux', 'Linux'),
        ('windows', 'Windows'),
    ]
    
    name = models.CharField(max_length=200)
    playbook_type = models.CharField(max_length=10, choices=PLAYBOOK_TYPE_CHOICES)
    os_family = models.CharField(max_length=10, choices=OS_FAMILY_CHOICES)
    file_path = models.CharField(max_length=500)
```

---

## Migration Guide

### For Existing Playbooks:

1. **Ensure all playbooks have correct metadata:**
   ```python
   # In Django admin or shell
   from playbooks.models import Playbook
   
   # Update host playbooks
   Playbook.objects.filter(file_path__contains='/host/').update(playbook_type='host')
   
   # Update group playbooks
   Playbook.objects.filter(file_path__contains='/group/').update(playbook_type='group')
   ```

2. **Set OS family:**
   ```python
   # Linux playbooks
   Playbook.objects.filter(name__contains='Linux').update(os_family='linux')
   
   # Windows playbooks
   Playbook.objects.filter(name__contains='Windows').update(os_family='windows')
   ```

### For Users:

**Old workflow (3 forms):**
```
1. Go to "Execute Playbook (Linux)" for hosts
2. Go to "Execute on Group" for groups
3. Different forms, different UX
```

**New workflow (1 form):**
```
1. Go to "Execute Playbook (Linux)"
2. Select Target Type: Host or Group
3. Same form, consistent UX
```

---

## Testing

### Test Host Execution:

1. Navigate to `/deploy/playbook/`
2. Select Target Type: **Host**
3. Select environment (optional)
4. Select group filter (optional)
5. Select a Linux host
6. Select a host playbook (loaded dynamically)
7. Check "Create snapshot" (optional)
8. Check "Schedule for later" (optional)
9. Click "Execute Playbook"

**Expected:** Playbook executes on selected host

### Test Group Execution:

1. Navigate to `/deploy/playbook/`
2. Select Target Type: **Group**
3. Select environment (optional)
4. Select a group
5. Select a group playbook (loaded dynamically)
6. Snapshot checkbox should be hidden
7. Check "Schedule for later" (optional)
8. Click "Execute Playbook"

**Expected:** Playbook executes on all Linux hosts in group

### Test Windows:

Same steps as above, but use `/deploy/playbook/windows/`

---

## Benefits Summary

✅ **Simplified Navigation**
- 2 forms instead of 3
- Clear OS separation (Linux/Windows)
- Intuitive target type selection

✅ **Consistent UX**
- Same structure for Linux and Windows
- Same behavior and features
- Easier to learn and use

✅ **Better Code Organization**
- Less duplication
- Easier to maintain
- Single source of truth for each OS

✅ **Enhanced Features**
- Dynamic playbook loading
- Scheduled execution
- Smart filtering
- Snapshot support (hosts only)

✅ **Future-Proof**
- Easy to add new features
- Scalable architecture
- Clear separation of concerns

---

## Files Modified

### Templates:
- ✅ `templates/deploy/deploy_playbook_form.html` - Rewritten
- ✅ `templates/deploy/deploy_playbook_windows_form.html` - Already unified
- ✅ `templates/base/sidebar.html` - Removed redundant menu item

### Views:
- ✅ `deploy/views_playbook.py` - Added target_type support
- ✅ `deploy/views_playbook_windows.py` - Already supports target_type

### URLs:
- ✅ `deploy/urls.py` - Added get_playbooks endpoint

### Backups:
- 📦 `templates/deploy/deploy_playbook_form_old.html`
- 📦 `deploy/views_playbook_old.py`

---

## Future Enhancements

1. **Background Task Queue**
   - Use Celery for scheduled execution
   - Real-time progress updates
   - Email notifications

2. **Bulk Operations**
   - Select multiple hosts
   - Execute on multiple groups
   - Parallel execution

3. **Playbook Templates**
   - Variable substitution
   - Custom parameters per execution
   - Save execution profiles

4. **Advanced Scheduling**
   - Recurring executions
   - Maintenance windows
   - Dependency chains

---

## Conclusion

The playbook form unification provides a cleaner, more intuitive interface for executing Ansible playbooks on both Linux and Windows hosts. By consolidating functionality into two unified forms (one per OS), we've eliminated redundancy, improved consistency, and created a more maintainable codebase.

**Key Takeaway:** One form per OS, with smart target type selection, is better than multiple forms with overlapping functionality.
