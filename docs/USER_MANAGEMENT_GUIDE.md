# User Management System - Quick Guide

## Overview
Complete user management system integrated into Diaken platform. Allows administrators to create, edit, and manage user accounts including password resets.

---

## Access
**Location:** Settings → Users  
**URL:** `/users/`  
**Required Permission:** Staff or Superuser

---

## Features

### 1. User List
- View all users in the system
- See user status (Active/Inactive)
- View permissions (User/Staff/Superuser)
- See last login time
- Quick actions for each user

### 2. Create User
**Path:** Settings → Users → Create New User

**Required Fields:**
- Username (unique)
- Password (minimum 8 characters)

**Optional Fields:**
- Email
- First Name
- Last Name

**Permissions:**
- ☐ Staff Status - Can access admin interface
- ☐ Superuser Status - Has all permissions

**Example:**
```
Username: jdoe
Password: SecurePass123!
Email: jdoe@company.com
First Name: John
Last Name: Doe
☑ Staff Status
☐ Superuser Status
```

### 3. Edit User
**Path:** Settings → Users → [Edit Icon]

**Can Modify:**
- Email
- First Name
- Last Name
- Staff Status
- Superuser Status
- Active Status

**Cannot Modify:**
- Username (readonly)
- Password (use Reset Password instead)

### 4. Reset Password
**Path:** Settings → Users → [Key Icon]

**Use When:**
- User forgets password
- Security breach
- Initial setup

**Process:**
1. Click key icon for user
2. Enter new password
3. Confirm password
4. Save

**Password Requirements:**
- Minimum 8 characters
- Mix of uppercase/lowercase recommended
- Include numbers and special characters
- Avoid common words

**Important:** Communicate new password securely to user

### 5. Toggle Active Status
**Path:** Settings → Users → [Ban/Check Icon]

**Activate User:**
- Click check icon
- User can log in

**Deactivate User:**
- Click ban icon
- User cannot log in
- Account preserved

**Use Cases:**
- Temporarily disable account
- Employee on leave
- Security concerns
- Preserve historical data

### 6. Delete User
**Path:** Settings → Users → [Trash Icon]

**Warning:** Permanent action!

**Process:**
1. Click trash icon
2. Review user information
3. Confirm deletion

**What Happens:**
- User account permanently removed
- Cannot log in
- Historical records may reference user
- Cannot be undone

**Alternative:** Consider deactivating instead

---

## User Roles

### Regular User
- Can log in
- Access basic features
- Cannot manage other users

### Staff User
- All regular user permissions
- Can access Settings
- Can manage other users
- Can manage system configuration

### Superuser
- All staff permissions
- Full system access
- Can manage all users
- Can access Django admin

---

## Common Scenarios

### Scenario 1: New Employee
```
1. Settings → Users → Create New User
2. Enter: username, password, email, name
3. Set permissions (usually Staff)
4. Save
5. Provide credentials to employee
```

### Scenario 2: Forgotten Password
```
1. Settings → Users
2. Find user in list
3. Click key icon (Reset Password)
4. Enter new password twice
5. Save
6. Communicate new password securely
```

### Scenario 3: Employee Leaving
```
Option A (Recommended): Deactivate
1. Settings → Users
2. Click ban icon for user
3. Confirm
4. Account disabled, data preserved

Option B: Delete
1. Settings → Users
2. Click trash icon
3. Confirm deletion
4. Account permanently removed
```

### Scenario 4: Change Permissions
```
1. Settings → Users
2. Click edit icon for user
3. Check/uncheck Staff or Superuser
4. Save
```

---

## Security Best Practices

### Password Management
- Use strong passwords (8+ characters)
- Mix uppercase, lowercase, numbers, symbols
- Don't reuse passwords
- Change default passwords immediately
- Use password manager

### Account Management
- Review user list regularly
- Deactivate unused accounts
- Remove accounts of departed employees
- Audit last login times
- Limit superuser accounts

### Access Control
- Grant minimum necessary permissions
- Regular users for most staff
- Staff for administrators
- Superuser only when needed
- Review permissions quarterly

---

## Troubleshooting

### Cannot Access User Management
**Problem:** "Permission Denied" error  
**Solution:** You need Staff or Superuser status. Contact your administrator.

### Cannot Create User
**Problem:** "Username already exists"  
**Solution:** Choose a different username. Usernames must be unique.

### Password Reset Not Working
**Problem:** Passwords don't match  
**Solution:** Ensure both password fields are identical.

### Cannot Deactivate User
**Problem:** "Cannot deactivate your own account"  
**Solution:** You cannot deactivate yourself. Ask another administrator.

### User Still Can't Log In
**Problem:** Password reset but user can't log in  
**Solution:** 
1. Check if account is Active
2. Verify password was communicated correctly
3. Check for typos in username

---

## API Endpoints

```
GET  /users/                      - List all users
GET  /users/create/               - Create user form
POST /users/create/               - Create user action
GET  /users/<id>/edit/            - Edit user form
POST /users/<id>/edit/            - Edit user action
GET  /users/<id>/reset-password/  - Reset password form
POST /users/<id>/reset-password/  - Reset password action
GET  /users/<id>/toggle-active/   - Toggle active status
GET  /users/<id>/delete/          - Delete confirmation
POST /users/<id>/delete/          - Delete user action
```

---

## Audit Trail

All user management actions are logged:
- User creation
- User updates
- Password resets
- Status changes
- User deletions

**Log Location:** Django logs  
**Log Level:** INFO

**Example Log Entries:**
```
INFO: User jdoe created by admin
INFO: Password reset for user jdoe by admin
INFO: User jdoe deactivated by admin
INFO: User jdoe deleted by admin
```

---

## Integration

### With Existing System
- Uses Django's built-in User model
- Compatible with existing authentication
- Works with current permission system
- Integrates with sidebar navigation

### With Other Features
- Users can deploy VMs
- Users can execute playbooks
- Users can schedule tasks
- Users can manage inventory

---

## Tips & Tricks

### Quick User Creation
1. Keep a template password for new users
2. Ask them to change on first login
3. Use email as username for easy remember

### Bulk Operations
- Currently manual (one at a time)
- Consider Django admin for bulk operations
- Or use management commands

### Password Policy
- Enforce minimum length (8 chars)
- Consider password expiration
- Implement password history
- Use two-factor authentication (future)

---

## Support

**Documentation:** `/opt/www/app/USER_MANAGEMENT_GUIDE.md`  
**System Diagrams:** `/opt/www/app/diagrams.md`  
**Session Summary:** `/opt/www/app/SESSION_SUMMARY.md`

**For Issues:**
1. Check this guide
2. Review error messages
3. Check Django logs
4. Contact system administrator

---

**Last Updated:** 2025-10-03  
**Version:** 1.0.0  
**Platform:** Diaken
