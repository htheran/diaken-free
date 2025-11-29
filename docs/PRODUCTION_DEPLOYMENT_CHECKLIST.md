# ✅ Production Deployment Checklist

## 🎯 Pre-Deployment Verification

### ✅ Code Quality (COMPLETADO)
- [x] All debug print statements removed (74 total)
- [x] Structured logging implemented
- [x] No hardcoded credentials
- [x] Production settings file created
- [x] .gitignore comprehensive (92 patterns)
- [x] Security documentation complete

### 📦 Next Steps for Deployment

---

## Step 1: Push to GitHub

```bash
cd /opt/www/app

# Verify changes are committed
git log --oneline -1

# Push to GitHub
git push origin main

# Verify push
git status
```

**Expected output**: `Your branch is up to date with 'origin/main'`

---

## Step 2: Prepare Production Server

### 2.1 Server Requirements

**Minimum specs**:
- OS: Oracle Linux 9.6 (x86_64)
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB
- Network: Internet access

**Required packages**:
- Python 3.9+
- Apache httpd with mod_wsgi
- govc CLI
- Ansible 2.14+
- Git

### 2.2 Clone Repository on Server

```bash
# On production server
ssh user@your-server.example.com

# Clone repository
cd /opt/www
sudo git clone https://github.com/YOUR_USER/YOUR_REPO.git diaken
cd diaken
```

---

## Step 3: Run Deployment Script

```bash
# Download and edit deployment script
sudo nano deploy_production.sh

# Update these variables:
# - GITHUB_REPO="https://github.com/YOUR_USER/YOUR_REPO.git"
# - SERVER_NAME="your-server.example.com"
# - SERVER_IP="10.100.x.x"

# Run deployment
sudo bash deploy_production.sh
```

**What the script does**:
1. Installs all required packages
2. Creates Python virtual environment
3. Installs Python dependencies
4. Creates directory structure
5. Configures Apache with mod_wsgi
6. Sets SELinux contexts
7. Configures firewall
8. Creates Django superuser
9. Runs migrations
10. Collects static files

---

## Step 4: Configure Environment Variables

### 4.1 Generate SECRET_KEY

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Save this key securely!**

### 4.2 Edit Apache Configuration

```bash
sudo nano /etc/httpd/conf.d/diaken.conf
```

**Add environment variables**:

```apache
<VirtualHost *:80>
    ServerName your-server.example.com
    ServerAdmin admin@example.com
    
    # Django Environment Variables
    SetEnv DJANGO_SECRET_KEY "YOUR-GENERATED-SECRET-KEY-HERE"
    SetEnv DJANGO_ALLOWED_HOSTS "your-server.example.com,10.100.x.x"
    SetEnv DJANGO_CSRF_TRUSTED_ORIGINS "http://your-server.example.com"
    
    # GOVC Variables (VMware CLI)
    SetEnv GOVC_URL "vcenter.example.com"
    SetEnv GOVC_USERNAME "administrator@vsphere.local"
    SetEnv GOVC_PASSWORD "YOUR-VCENTER-PASSWORD"
    SetEnv GOVC_INSECURE "true"
    
    # Security Settings (if using HTTPS)
    # SetEnv DJANGO_SECURE_SSL_REDIRECT "True"
    # SetEnv DJANGO_SESSION_COOKIE_SECURE "True"
    # SetEnv DJANGO_CSRF_COOKIE_SECURE "True"
    
    # WSGI Configuration
    WSGIDaemonProcess diaken python-home=/opt/www/diaken/venv python-path=/opt/www/diaken
    WSGIProcessGroup diaken
    WSGIScriptAlias / /opt/www/diaken/diaken/wsgi.py
    WSGIPassAuthorization On
    
    # Static and Media Files
    Alias /static /opt/www/diaken/staticfiles
    Alias /media /opt/www/diaken/media
    
    <Directory /opt/www/diaken/staticfiles>
        Require all granted
    </Directory>
    
    <Directory /opt/www/diaken/media>
        Require all granted
    </Directory>
    
    <Directory /opt/www/diaken/diaken>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    
    # Logging
    ErrorLog /opt/www/logs/apache_error.log
    CustomLog /opt/www/logs/apache_access.log combined
</VirtualHost>
```

### 4.3 Update wsgi.py for Production

```bash
sudo nano /opt/www/diaken/diaken/wsgi.py
```

**Change settings module**:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings_production')
```

---

## Step 5: Set File Permissions

```bash
# Set ownership
sudo chown -R apache:apache /opt/www/diaken
sudo chown -R apache:apache /opt/www/logs

# Set permissions
sudo find /opt/www/diaken -type d -exec chmod 755 {} \;
sudo find /opt/www/diaken -type f -exec chmod 644 {} \;
sudo chmod 660 /opt/www/diaken/db.sqlite3
sudo chmod 600 /opt/www/diaken/media/ssh/*.pem

# SELinux contexts
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/www/diaken(/.*)?"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/www/diaken/db.sqlite3"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/www/diaken/media(/.*)?"
sudo semanage fcontext -a -t httpd_log_t "/opt/www/logs(/.*)?"
sudo restorecon -Rv /opt/www/
```

---

## Step 6: Security Checks

### 6.1 Run Django Security Check

```bash
cd /opt/www/diaken
sudo -u apache /opt/www/diaken/venv/bin/python manage.py check --deploy --settings=diaken.settings_production
```

**Expected**: No critical warnings (some warnings are expected for first deployment)

### 6.2 Verify Firewall

```bash
sudo firewall-cmd --list-all
```

**Should show**:
- services: http https ssh

### 6.3 Check SELinux

```bash
sudo getenforce
```

**Should return**: `Enforcing`

---

## Step 7: Start Services

```bash
# Restart Apache
sudo systemctl restart httpd

# Check status
sudo systemctl status httpd

# Enable on boot
sudo systemctl enable httpd
```

---

## Step 8: Verify Deployment

### 8.1 Test Local Access

```bash
# Test HTTP
curl http://localhost/

# Should return HTML (Django login page)
```

### 8.2 Test Remote Access

From your workstation:

```bash
# Test HTTP
curl http://your-server.example.com/

# Open in browser
firefox http://your-server.example.com/
```

### 8.3 Check Logs

```bash
# Django logs
sudo tail -f /opt/www/logs/django.log

# Deployment logs
sudo tail -f /opt/www/logs/deployment.log

# Apache error logs
sudo tail -f /opt/www/logs/apache_error.log
```

### 8.4 Login and Test

1. Navigate to: `http://your-server.example.com/admin/`
2. Login with Django superuser credentials
3. Test VM deployment functionality

---

## Step 9: HTTPS Setup (Optional but Recommended)

### 9.1 Generate SSL Certificate

**Option A: Self-Signed (Testing)**

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/pki/tls/private/diaken.key \
  -out /etc/pki/tls/certs/diaken.crt
```

**Option B: Let's Encrypt (Production)**

```bash
sudo dnf install -y certbot python3-certbot-apache
sudo certbot --apache -d your-server.example.com
```

### 9.2 Configure Apache SSL

Create `/etc/httpd/conf.d/diaken-ssl.conf`:

```apache
<VirtualHost *:443>
    ServerName your-server.example.com
    ServerAdmin admin@example.com
    
    SSLEngine on
    SSLCertificateFile /etc/pki/tls/certs/diaken.crt
    SSLCertificateKeyFile /etc/pki/tls/private/diaken.key
    
    # Strong SSL Configuration
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5:!3DES
    SSLHonorCipherOrder on
    
    # HSTS
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    
    # Security Headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "DENY"
    Header always set X-XSS-Protection "1; mode=block"
    
    # Environment Variables (same as HTTP)
    SetEnv DJANGO_SECRET_KEY "YOUR-SECRET-KEY"
    SetEnv DJANGO_ALLOWED_HOSTS "your-server.example.com"
    SetEnv DJANGO_SECURE_SSL_REDIRECT "True"
    SetEnv DJANGO_SESSION_COOKIE_SECURE "True"
    SetEnv DJANGO_CSRF_COOKIE_SECURE "True"
    SetEnv DJANGO_CSRF_TRUSTED_ORIGINS "https://your-server.example.com"
    
    # ... (rest of WSGI configuration same as HTTP)
</VirtualHost>

# Redirect HTTP to HTTPS
<VirtualHost *:80>
    ServerName your-server.example.com
    Redirect permanent / https://your-server.example.com/
</VirtualHost>
```

### 9.3 Restart Apache

```bash
sudo systemctl restart httpd
```

---

## Step 10: Post-Deployment Tasks

### 10.1 Create Backup Script

```bash
sudo nano /opt/www/scripts/backup_full.sh
```

See `SECURITY.md` for full backup script.

```bash
sudo chmod +x /opt/www/scripts/backup_full.sh

# Test backup
sudo /opt/www/scripts/backup_full.sh
```

### 10.2 Setup Automated Backups

```bash
sudo crontab -e
```

Add:
```
0 2 * * * /opt/www/scripts/backup_full.sh >> /opt/www/logs/backup.log 2>&1
```

### 10.3 Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/diaken
```

Add:
```
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

### 10.4 Set Up Monitoring

```bash
# Monitor logs
sudo tail -f /opt/www/logs/django.log
sudo tail -f /opt/www/logs/deployment.log
sudo tail -f /opt/www/logs/security.log

# Check disk space
df -h /opt/www

# Check Apache processes
ps aux | grep httpd
```

---

## 📊 Verification Checklist

Before going live, verify:

- [ ] All environment variables set in Apache config
- [ ] SECRET_KEY is unique and secure (not default)
- [ ] ALLOWED_HOSTS includes production domain/IP
- [ ] Django security check passes with no critical warnings
- [ ] Apache starts without errors
- [ ] Web interface loads correctly
- [ ] Can login to Django admin
- [ ] Can deploy a test VM successfully
- [ ] Logs are being written to /opt/www/logs/
- [ ] Firewall allows HTTP/HTTPS only
- [ ] SELinux is enforcing
- [ ] File permissions are correct
- [ ] Backups are scheduled
- [ ] Log rotation is configured

---

## 🚨 Troubleshooting

### Apache won't start

```bash
# Check error logs
sudo journalctl -xeu httpd
sudo tail -f /opt/www/logs/apache_error.log

# Test configuration
sudo apachectl configtest
```

### Permission denied errors

```bash
# Reset permissions
sudo chown -R apache:apache /opt/www/diaken
sudo restorecon -Rv /opt/www/
```

### 500 Internal Server Error

```bash
# Check Django logs
sudo tail -f /opt/www/logs/django.log

# Check Apache error log
sudo tail -f /opt/www/logs/apache_error.log

# Verify wsgi.py has production settings
grep DJANGO_SETTINGS_MODULE /opt/www/diaken/diaken/wsgi.py
```

### Cannot connect to vCenter

```bash
# Verify GOVC environment variables
sudo grep GOVC /etc/httpd/conf.d/diaken.conf

# Test govc manually
export GOVC_URL="vcenter.example.com"
export GOVC_USERNAME="administrator@vsphere.local"
export GOVC_PASSWORD="your-password"
export GOVC_INSECURE="true"
govc about
```

---

## 📞 Support Resources

- **Security Guide**: `SECURITY.md`
- **Hardening Summary**: `SECURITY_HARDENING_SUMMARY.md`
- **Deployment Guide**: `DEPLOYMENT_PRODUCCION.md`
- **Quick Start**: `QUICK_START_PRODUCCION.md`

---

## ✅ Deployment Sign-Off

**Deployment Date**: _______________  
**Deployed by**: _______________  
**Server**: _______________  
**Version**: 1.0 Production Hardened  

**Verification**:
- [ ] All checks passed
- [ ] Production ready
- [ ] Monitoring active
- [ ] Backups configured

**Approved by**: _______________  
**Date**: _______________

---

**Next Steps After Deployment**:
1. Monitor logs for first 24 hours
2. Test all functionality
3. Train users
4. Document any issues
5. Schedule security updates

**Maintenance Schedule**:
- **Daily**: Monitor logs
- **Weekly**: Review security logs
- **Monthly**: Update packages, rotate SSH keys (if needed)
- **Quarterly**: Security audit, rotate passwords
- **Annually**: Review and update documentation
