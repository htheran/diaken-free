# 🔐 Security Guidelines - Diaken Project

## Overview

This document outlines security best practices and configurations for the Diaken VMware VM automation deployment system.

---

## 🚨 Critical Security Checklist

### Before Production Deployment

- [ ] **Change SECRET_KEY** in production settings
- [ ] **Set DEBUG = False** (automatically set in settings_production.py)
- [ ] **Configure ALLOWED_HOSTS** properly
- [ ] **Enable HTTPS/SSL** and set security headers
- [ ] **Set up firewall rules** (allow only 80/443)
- [ ] **Configure SELinux** in enforcing mode
- [ ] **Change default database credentials** (if using PostgreSQL)
- [ ] **Rotate SSH keys** for VM deployment
- [ ] **Set strong passwords** for Django admin users
- [ ] **Configure email alerts** for security events
- [ ] **Set up log rotation** and monitoring
- [ ] **Backup encryption keys** and credentials securely

---

## 🔑 Secret Management

### SECRET_KEY

**Development** (`settings.py`):
- Uses a fixed insecure key (acceptable for development only)
- **NEVER use this key in production**

**Production** (`settings_production.py`):
```bash
# Generate a new secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Set as environment variable
export DJANGO_SECRET_KEY='your-generated-secret-key-here'
```

**Apache httpd configuration**:
```apache
<VirtualHost *:80>
    SetEnv DJANGO_SECRET_KEY "your-generated-secret-key-here"
    # ... other directives
</VirtualHost>
```

### Sensitive Environment Variables

Always set these via environment variables in production:

```bash
# Django settings
export DJANGO_SECRET_KEY="..."
export DJANGO_ALLOWED_HOSTS="example.com,www.example.com"
export DJANGO_CSRF_TRUSTED_ORIGINS="https://example.com"

# Database (if using PostgreSQL)
export DB_NAME="diaken"
export DB_USER="diaken_user"
export DB_PASSWORD="strong-password-here"
export DB_HOST="localhost"
export DB_PORT="5432"

# Email notifications
export EMAIL_HOST="smtp.example.com"
export EMAIL_PORT="587"
export EMAIL_HOST_USER="noreply@example.com"
export EMAIL_HOST_PASSWORD="email-password-here"
export EMAIL_USE_TLS="True"

# GOVC (VMware CLI)
export GOVC_URL="vcenter.example.com"
export GOVC_USERNAME="automation@vsphere.local"
export GOVC_PASSWORD="vcenter-password-here"
export GOVC_INSECURE="true"

# SSL/HTTPS
export DJANGO_SECURE_SSL_REDIRECT="True"
export DJANGO_SESSION_COOKIE_SECURE="True"
export DJANGO_CSRF_COOKIE_SECURE="True"
export DJANGO_SECURE_HSTS_SECONDS="31536000"  # 1 year
export DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS="True"
export DJANGO_SECURE_HSTS_PRELOAD="True"
```

---

## 🔒 HTTPS/SSL Configuration

### Generate Self-Signed Certificate (Testing)

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/pki/tls/private/diaken.key \
  -out /etc/pki/tls/certs/diaken.crt
```

### Apache SSL Configuration

```apache
<VirtualHost *:443>
    ServerName your-server.example.com
    
    SSLEngine on
    SSLCertificateFile /etc/pki/tls/certs/diaken.crt
    SSLCertificateKeyFile /etc/pki/tls/private/diaken.key
    
    # Strong SSL configuration
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5:!3DES
    SSLHonorCipherOrder on
    
    # HSTS (mod_headers is required)
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    
    # Rest of configuration...
    WSGIDaemonProcess diaken python-home=/opt/www/diaken/venv python-path=/opt/www/diaken
    WSGIProcessGroup diaken
    WSGIScriptAlias / /opt/www/diaken/diaken/wsgi.py
    
    # ... (see DEPLOYMENT_PRODUCCION.md for full config)
</VirtualHost>
```

### Redirect HTTP to HTTPS

```apache
<VirtualHost *:80>
    ServerName your-server.example.com
    Redirect permanent / https://your-server.example.com/
</VirtualHost>
```

---

## 🛡️ Database Security

### SQLite (Development)

- Default for development/testing
- File permissions: `660` (owner: apache, group: apache)
- Location: `/opt/www/diaken/db.sqlite3`

**Secure permissions**:
```bash
sudo chown apache:apache /opt/www/diaken/db.sqlite3
sudo chmod 660 /opt/www/diaken/db.sqlite3
```

### PostgreSQL (Production Recommended)

```bash
# Install PostgreSQL
sudo dnf install -y postgresql-server postgresql-contrib

# Initialize database
sudo postgresql-setup --initdb

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE diaken;
CREATE USER diaken_user WITH ENCRYPTED PASSWORD 'strong-password-here';
GRANT ALL PRIVILEGES ON DATABASE diaken TO diaken_user;
\q
```

**Update settings_production.py**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'diaken'),
        'USER': os.environ.get('DB_USER', 'diaken_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

---

## 🔐 Password Policies

### Django User Passwords

Production settings enforce strong passwords:
- Minimum length: **12 characters**
- Cannot be similar to user attributes
- Cannot be a common password
- Cannot be entirely numeric

### vCenter/SSH Credentials

Stored encrypted in database:
- Use Django's password validators
- Never log passwords in clear text
- Rotate credentials regularly (every 90 days recommended)

### SSH Keys for VM Deployment

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "diaken-automation" -f /opt/www/diaken/media/ssh/diaken_deploy.pem

# Set restrictive permissions
chmod 600 /opt/www/diaken/media/ssh/diaken_deploy.pem
chown apache:apache /opt/www/diaken/media/ssh/diaken_deploy.pem

# Public key should be added to VM templates
cat /opt/www/diaken/media/ssh/diaken_deploy.pem.pub
```

**Rotation policy**: Rotate SSH keys every 6 months

---

## 🚫 File Permissions

### Application Files

```bash
# Project directory
sudo chown -R apache:apache /opt/www/diaken
sudo find /opt/www/diaken -type d -exec chmod 755 {} \;
sudo find /opt/www/diaken -type f -exec chmod 644 {} \;

# Executable scripts
sudo chmod +x /opt/www/diaken/manage.py

# Database (if SQLite)
sudo chmod 660 /opt/www/diaken/db.sqlite3

# Media directory (uploaded files)
sudo chmod 750 /opt/www/diaken/media
sudo chmod 750 /opt/www/diaken/media/ssh

# SSH keys
sudo chmod 600 /opt/www/diaken/media/ssh/*.pem

# Logs
sudo mkdir -p /opt/www/logs
sudo chown apache:apache /opt/www/logs
sudo chmod 755 /opt/www/logs
```

### SELinux Contexts

```bash
# Set SELinux contexts
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/www/diaken(/.*)?"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/www/diaken/db.sqlite3"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/www/diaken/media(/.*)?"
sudo semanage fcontext -a -t httpd_log_t "/opt/www/logs(/.*)?"
sudo restorecon -Rv /opt/www/
```

---

## 🔥 Firewall Configuration

### Oracle Linux / RHEL

```bash
# Allow HTTP and HTTPS only
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

### iptables (Alternative)

```bash
# Allow HTTP/HTTPS
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Block all other incoming
sudo iptables -A INPUT -j DROP

# Save rules
sudo service iptables save
```

---

## 📊 Logging and Monitoring

### Log Files

All logs are stored in `/opt/www/logs/`:

- `django.log` - General Django logs
- `deployment.log` - VM deployment operations (detailed)
- `security.log` - Security-related events
- `apache_access.log` - HTTP access logs
- `apache_error.log` - Apache error logs

### Log Rotation

Create `/etc/logrotate.d/diaken`:

```bash
/opt/www/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 apache apache
    sharedscripts
    postrotate
        systemctl reload httpd > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring

```bash
# Monitor deployment logs in real-time
sudo tail -f /opt/www/logs/deployment.log

# Monitor security events
sudo tail -f /opt/www/logs/security.log

# Monitor Apache errors
sudo tail -f /opt/www/logs/apache_error.log

# Check failed login attempts
sudo grep "Failed login" /opt/www/logs/django.log
```

---

## 🚨 Security Headers

Set in `settings_production.py`:

```python
# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Apache Additional Headers

Add to Apache configuration:

```apache
# Security headers
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
```

---

## 🔍 Security Auditing

### Regular Security Checks

```bash
# Check for security updates
sudo dnf check-update

# Update all packages
sudo dnf update -y

# Audit file permissions
sudo find /opt/www/diaken -type f -perm /o+w -exec ls -la {} \;

# Check for suspicious processes
ps aux | grep apache

# Review failed authentication attempts
sudo grep "authentication failure" /var/log/secure

# Check Django admin access
sudo grep "admin" /opt/www/logs/django.log | grep "login"
```

### Django Security Check

```bash
cd /opt/www/diaken
sudo -u apache /opt/www/diaken/venv/bin/python manage.py check --deploy --settings=diaken.settings_production
```

---

## 📝 Backup and Disaster Recovery

### Database Backups

```bash
# SQLite backup
sudo cp /opt/www/diaken/db.sqlite3 /opt/www/backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# PostgreSQL backup
sudo -u postgres pg_dump diaken > /opt/www/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

### Full Backup Script

Create `/opt/www/scripts/backup_full.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/www/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
cp /opt/www/diaken/db.sqlite3 "$BACKUP_DIR/db_$DATE.sqlite3"

# Backup media files
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" /opt/www/diaken/media

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/www/diaken/diaken/settings_production.py /etc/httpd/conf.d/diaken.conf

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.sqlite3" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "✅ Backup completed: $DATE"
```

### Automated Backups

```bash
# Add to crontab
sudo crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/www/scripts/backup_full.sh >> /opt/www/logs/backup.log 2>&1
```

---

## ⚠️ Incident Response

### If Compromised

1. **Immediately disconnect from network**
   ```bash
   sudo systemctl stop httpd
   sudo systemctl stop network
   ```

2. **Preserve evidence**
   ```bash
   sudo tar -czf /tmp/incident_$(date +%Y%m%d).tar.gz /opt/www/logs/ /var/log/httpd/ /var/log/secure
   ```

3. **Review logs for suspicious activity**
   ```bash
   sudo grep -i "fail\|error\|unauthorized" /opt/www/logs/*.log
   sudo last
   sudo lastb
   ```

4. **Change all credentials**
   - Django SECRET_KEY
   - Database passwords
   - vCenter credentials
   - SSH keys
   - Admin user passwords

5. **Restore from clean backup**

6. **Update and patch all software**

7. **Notify security team**

---

## 📞 Security Contacts

- **System Administrator**: admin@example.com
- **Security Team**: security@example.com
- **Emergency Hotline**: +1-xxx-xxx-xxxx

---

## 📚 Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Apache Security Tips](https://httpd.apache.org/docs/2.4/misc/security_tips.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Last Updated**: 2025-10-16  
**Version**: 1.0  
**Author**: htheran
