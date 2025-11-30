# Diaken Installation Guide

## Quick Start (Recommended)

### For Ubuntu/Debian:
```bash
wget https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken-nginx.sh
chmod +x install-diaken-nginx.sh
sudo bash install-diaken-nginx.sh
```

### For RedHat/CentOS/Rocky Linux:
```bash
wget https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken-nginx.sh
chmod +x install-diaken-nginx.sh
sudo bash install-diaken-nginx.sh
```

**This script works on both Debian and RedHat-based systems!**

---

## Installation Methods

### Method 1: One-Line Install (Easiest)

**Ubuntu/Debian:**
```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken-nginx.sh | sudo bash
```

**RedHat/CentOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken-nginx.sh | sudo bash
```

### Method 2: Clone and Install

```bash
git clone https://github.com/htheran/diaken-free.git
cd diaken-free
sudo bash install-diaken-nginx.sh
```

### Method 3: RPM Package (RedHat/CentOS only)

**Coming soon!** We're working on a proper RPM package.

For now, use Method 1 or 2 above.

---

## What the Installer Does

The `install-diaken-nginx.sh` script will:

1. ✅ Detect your OS (Ubuntu/Debian or RedHat/CentOS)
2. ✅ Install all required dependencies
3. ✅ Create diaken user and directories
4. ✅ Set up Python virtual environment
5. ✅ Install Python packages
6. ✅ Configure database (SQLite by default)
7. ✅ Run Django migrations
8. ✅ Create admin superuser
9. ✅ Collect static files
10. ✅ Configure Nginx
11. ✅ Set up systemd services
12. ✅ Generate SSL certificate
13. ✅ Configure firewall
14. ✅ Start all services

---

## After Installation

### Access Diaken

```
https://YOUR_SERVER_IP
```

**Default credentials:**
- Username: `admin`
- Password: `admin123` (change immediately!)

### Service Management

```bash
# Check status
sudo systemctl status diaken

# Restart
sudo systemctl restart diaken

# View logs
sudo journalctl -u diaken -f
```

### Verify Installation

```bash
sudo bash /opt/diaken/sc/check_installation.sh
```

---

## System Requirements

### Minimum:
- **OS**: Ubuntu 20.04+ or RHEL/CentOS 8+
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB

### Recommended:
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 50+ GB SSD

---

## Supported Operating Systems

✅ **Ubuntu** 20.04, 22.04, 24.04  
✅ **Debian** 11, 12  
✅ **RHEL** 8, 9  
✅ **CentOS** 8, 9 Stream  
✅ **Rocky Linux** 8, 9  
✅ **AlmaLinux** 8, 9  
✅ **Fedora** 38+

---

## Troubleshooting

### Installation fails

Check logs:
```bash
tail -100 /var/log/diaken/error.log
```

### Service won't start

```bash
sudo systemctl status diaken
sudo journalctl -u diaken -n 50
```

### Can't access web interface

Check firewall:
```bash
sudo firewall-cmd --list-all  # RedHat/CentOS
sudo ufw status              # Ubuntu/Debian
```

---

## Uninstall

```bash
# Stop services
sudo systemctl stop diaken diaken-celery diaken-celery-beat

# Remove files
sudo rm -rf /opt/diaken
sudo rm -rf /var/log/diaken
sudo rm /etc/systemd/system/diaken*.service
sudo rm /etc/nginx/sites-available/diaken
sudo rm /etc/nginx/sites-enabled/diaken

# Remove user
sudo userdel -r diaken
```

---

## Support

- **Documentation**: https://github.com/htheran/diaken-free
- **Issues**: https://github.com/htheran/diaken-free/issues

---

## Note About install-diaken-rpm.sh

⚠️ **Do NOT use `install-diaken-rpm.sh`** - it has issues and gets stuck.

✅ **Use `install-diaken-nginx.sh`** instead - it works perfectly on both Debian and RedHat systems!

The `install-diaken-nginx.sh` script is universal and works on all supported Linux distributions.
