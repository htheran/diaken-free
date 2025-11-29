# 🚀 Diaken Installation Guide

## Quick Install (RedHat/CentOS/Rocky Linux)

### One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo bash
```

### Manual Install

```bash
# Download the installer
wget https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh

# Make it executable
chmod +x install-diaken.sh

# Run the installer
sudo ./install-diaken.sh
```

---

## What the Installer Does

The automated installer will:

✅ **System Preparation**
- Check OS compatibility (RedHat/CentOS/Rocky Linux)
- Install EPEL repository if not present
- Update system packages

✅ **Dependencies Installation**
- Git
- Python 3.12 (or 3.x available)
- Python pip and development tools
- GCC compiler and libraries
- Firewalld

✅ **Application Setup**
- Clone project from GitHub
- Create Python virtual environment
- Install all Python dependencies from requirements.txt
- Create required directories (logs, media, etc.)

✅ **Database Configuration**
- Run Django migrations
- Create SQLite database
- Collect static files

✅ **Security Setup**
- Create Django superuser (you'll be prompted)
- Configure firewall
- Open port 9090 permanently

✅ **Optional Services**
- Optionally create systemd service for auto-start

---

## Requirements

- **OS**: RedHat 8+, CentOS 8+, Rocky Linux 8+, AlmaLinux 8+
- **User**: Root or sudo access
- **Memory**: 2GB RAM minimum
- **Disk**: 5GB free space
- **Network**: Internet connection for package downloads

---

## Installation Process

### 1. Pre-Installation

The installer will ask for confirmation before starting:
```
Do you want to continue? (y/N):
```

### 2. During Installation

You'll be prompted to provide:

**Django Admin Credentials:**
- Username (e.g., `admin`)
- Password (typed twice for confirmation)
- Email (optional)

**Systemd Service (Optional):**
- Whether to create auto-start service

### 3. Installation Time

Typical installation takes **5-10 minutes** depending on:
- Internet speed
- System specifications
- Number of packages to install

---

## Post-Installation

### Starting Diaken

**Option 1: Manual Start**
```bash
cd /opt/diaken
source venv/bin/activate
python manage.py runserver 0.0.0.0:9090
```

**Option 2: Systemd Service** (if created)
```bash
sudo systemctl start diaken
sudo systemctl status diaken
```

### Accessing the Application

- **Web Interface**: `http://YOUR_SERVER_IP:9090`
- **Admin Panel**: `http://YOUR_SERVER_IP:9090/admin`

### Default Locations

```
Installation Directory:  /opt/diaken
Database:               /opt/diaken/db.sqlite3
Logs:                   /opt/diaken/logs/
Media Files:            /opt/diaken/media/
Virtual Environment:    /opt/diaken/venv/
```

---

## Firewall Configuration

The installer automatically:
- Starts `firewalld` service
- Opens port `9090/tcp` permanently
- Reloads firewall rules

**Verify firewall:**
```bash
sudo firewall-cmd --list-ports
```

**Manual firewall commands:**
```bash
# Open port
sudo firewall-cmd --permanent --add-port=9090/tcp
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

---

## Troubleshooting

### Python Not Found

If Python 3.12 is not available:
```bash
# The installer will use python3 instead
# Or install Python 3.12 manually:
sudo dnf install python3.12
```

### Port Already in Use

If port 9090 is occupied:
```bash
# Check what's using the port
sudo lsof -i :9090

# Or use a different port
python manage.py runserver 0.0.0.0:8080
```

### Permission Denied

Ensure you're running with sudo:
```bash
sudo ./install-diaken.sh
```

### Git Clone Fails

Check internet connection:
```bash
ping github.com
```

### Dependencies Installation Fails

Manually install core dependencies:
```bash
sudo dnf install -y git python3 python3-pip gcc
```

---

## Uninstallation

To completely remove Diaken:

```bash
# Stop service (if created)
sudo systemctl stop diaken
sudo systemctl disable diaken
sudo rm /etc/systemd/system/diaken.service

# Close firewall port
sudo firewall-cmd --permanent --remove-port=9090/tcp
sudo firewall-cmd --reload

# Remove installation directory
sudo rm -rf /opt/diaken

# Remove system packages (optional)
sudo dnf remove python3-pip
```

---

## Production Deployment

For production environments, consider:

### 1. Use Gunicorn/uWSGI
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:9090 diaken.wsgi:application
```

### 2. Setup Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:9090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /opt/diaken/staticfiles/;
    }
    
    location /media/ {
        alias /opt/diaken/media/;
    }
}
```

### 3. Use PostgreSQL
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'diaken',
        'USER': 'diaken_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. SSL/TLS Certificate
```bash
# Using Let's Encrypt
sudo dnf install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Support

- **GitHub**: https://github.com/htheran/diaken-free
- **Issues**: https://github.com/htheran/diaken-free/issues
- **Documentation**: See project README.md

---

## License

This project is licensed under the terms specified in the repository.

---

**Thank you for using Diaken!** 🎉
