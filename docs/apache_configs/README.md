# 🔧 Apache Configuration Files - Diaken Project

This directory contains secure Apache httpd configuration files for the Diaken project.

---

## 📁 Files

### `diaken.conf.secure`
**Secure Apache configuration without hardcoded secrets**

- ✅ NO hardcoded SECRET_KEY or sensitive data
- ✅ Security headers enabled
- ✅ File protections in place
- ✅ Directory listing disabled
- ✅ Proper WSGI configuration

---

## 🚀 Installation

### Step 1: Backup Current Configuration

```bash
sudo cp /etc/httpd/conf.d/diaken.conf /etc/httpd/conf.d/diaken.conf.backup
```

### Step 2: Install Secure Configuration

```bash
sudo cp /opt/www/app/diaken-pdn/docs/apache_configs/diaken.conf.secure \
        /etc/httpd/conf.d/diaken.conf
```

### Step 3: Test Configuration

```bash
sudo httpd -t
```

Should output: `Syntax OK`

### Step 4: Restart Apache

```bash
sudo systemctl restart httpd
```

### Step 5: Verify Application Works

```bash
curl -I http://your-server.example.com/
```

Should return `HTTP/1.1 200 OK` or redirect to login

---

## ⚠️ CRITICAL: Remove Hardcoded Secrets

The current `/etc/httpd/conf.d/diaken.conf` has **hardcoded SECRET_KEY**.

This **MUST** be removed immediately:

```bash
# Edit the file
sudo nano /etc/httpd/conf.d/diaken.conf

# Remove these lines:
# SetEnv DJANGO_SECRET_KEY "..."
# SetEnv DJANGO_ALLOWED_HOSTS "..."
# SetEnv DJANGO_CSRF_TRUSTED_ORIGINS "..."
```

**Why?**
- Django already loads these from `.env` file
- Hardcoding in Apache exposes secrets
- Anyone with Apache access can see them
- Contradicts Django security fixes

---

## 🔒 Security Features in diaken.conf.secure

### 1. No Hardcoded Secrets ✅
- Django loads from `.env` via python-dotenv
- Apache doesn't need SetEnv directives

### 2. Security Headers ✅
```apache
X-XSS-Protection: 1; mode=block
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: ...
Permissions-Policy: ...
```

### 3. File Protections ✅
- `.env` files blocked
- `.pyc` files blocked
- Backup files blocked
- `.git` directory blocked
- Scripts in media directory blocked

### 4. Directory Security ✅
- Directory listing disabled (`-Indexes`)
- CGI execution disabled (`-ExecCGI`)
- Only necessary HTTP methods allowed

### 5. WSGI Hardening ✅
- Process limits configured
- Deadlock timeout set
- Inactivity timeout set
- Maximum requests limit

---

## 🧪 Testing

### Test 1: Verify Django Loads .env

```bash
cd /opt/www/app/diaken-pdn
source venv/bin/activate
python manage.py shell

>>> from django.conf import settings
>>> print(len(settings.SECRET_KEY))
# Should print 50 (or similar length)
>>> exit()
```

### Test 2: Verify Security Headers

```bash
curl -I http://your-server.example.com/ | grep -E "X-|Content-Security"
```

Should show:
```
X-XSS-Protection: 1; mode=block
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: ...
```

### Test 3: Verify File Protections

```bash
# Try to access .env (should be denied)
curl http://your-server.example.com/.env
# Should return 403 Forbidden

# Try to access .pyc file (should be denied)
curl http://your-server.example.com/settings.pyc
# Should return 403 Forbidden
```

---

## 🔐 Optional: Separate Environment File

If you **must** use Apache SetEnv (not recommended), create a separate restricted file:

```bash
# Create restricted file
sudo touch /etc/httpd/conf.d/diaken-env.conf
sudo chmod 600 /etc/httpd/conf.d/diaken-env.conf
sudo chown root:root /etc/httpd/conf.d/diaken-env.conf

# Edit file
sudo nano /etc/httpd/conf.d/diaken-env.conf
```

Content:
```apache
# /etc/httpd/conf.d/diaken-env.conf
# Permissions: 600 (root only)

SetEnv DJANGO_SECRET_KEY "your-secret-key-from-env-file"
SetEnv DJANGO_ALLOWED_HOSTS "your-server.example.com,localhost"
SetEnv DJANGO_CSRF_TRUSTED_ORIGINS "https://your-server.example.com"
SetEnv ENCRYPTION_KEY "your-encryption-key-from-env-file"
```

**Note:** This is still less secure than Django loading from `.env`. Only use if absolutely necessary.

---

## 🌐 HTTPS Configuration

### Enable HTTPS (Recommended)

1. **Obtain SSL Certificate:**

```bash
# Option 1: Let's Encrypt (Free)
sudo dnf install certbot python3-certbot-apache
sudo certbot --apache -d your-server.example.com

# Option 2: Use institutional certificate
# Copy to /etc/ssl/httpd/
```

2. **Enable SSL Configuration:**

```bash
# Enable SSL config
sudo mv /etc/httpd/conf.d/diaken-pdn-ssl.conf.disabled \
        /etc/httpd/conf.d/diaken-pdn-ssl.conf

# Enable HTTP to HTTPS redirect
sudo mv /etc/httpd/conf.d/diaken-pdn-http-redirect.conf.disabled \
        /etc/httpd/conf.d/diaken-pdn-http-redirect.conf

# Test configuration
sudo httpd -t

# Restart Apache
sudo systemctl restart httpd
```

3. **Update Django Settings:**

Add to `.env`:
```bash
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-server.example.com
```

Add to `settings.py`:
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

---

## 📋 Checklist

Before going to production:

- [ ] Remove hardcoded SECRET_KEY from Apache config
- [ ] Install diaken.conf.secure
- [ ] Test Apache configuration (`httpd -t`)
- [ ] Verify Django loads .env correctly
- [ ] Test security headers
- [ ] Test file protections
- [ ] Obtain SSL certificate
- [ ] Enable HTTPS
- [ ] Configure HTTP to HTTPS redirect
- [ ] Update Django SSL settings
- [ ] Test HTTPS functionality

---

## 🆘 Troubleshooting

### Issue: Application doesn't load after removing SetEnv

**Solution:**
1. Verify `.env` file exists: `ls -la /opt/www/app/diaken-pdn/.env`
2. Verify Django can read it:
   ```bash
   cd /opt/www/app/diaken-pdn
   source venv/bin/activate
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SECRET_KEY loaded:', bool(os.getenv('DJANGO_SECRET_KEY')))"
   ```
3. Check Apache error log: `sudo tail -50 /opt/www/logs/apache_error.log`

### Issue: 500 Internal Server Error

**Solution:**
1. Check Apache error log
2. Verify WSGI module is loaded
3. Verify Python virtual environment path is correct
4. Test Django directly: `python manage.py runserver`

### Issue: Static files not loading

**Solution:**
1. Verify static files collected: `python manage.py collectstatic`
2. Check permissions: `ls -la /opt/www/app/diaken-pdn/staticfiles`
3. Verify Alias path in Apache config

---

## 📚 References

- [Apache Security Audit](../security_analysis/APACHE_SECURITY_AUDIT.md)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Apache Security Tips](https://httpd.apache.org/docs/2.4/misc/security_tips.html)
- [OWASP Secure Headers](https://owasp.org/www-project-secure-headers/)

---

**Last Updated:** October 16, 2025  
**Maintainer:** Diaken Security Team
