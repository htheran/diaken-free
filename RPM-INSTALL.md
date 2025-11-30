# Diaken RPM Installation Guide

## Overview

Diaken provides a professional RPM package for easy installation on RedHat-based distributions (RHEL, CentOS, Rocky Linux, AlmaLinux, Fedora).

## Features

✅ **Interactive Installation**
- Step-by-step guided setup
- Progress indicators
- User input validation
- Configuration summary

✅ **Security Hardened**
- SELinux compatible
- Systemd service isolation
- Secure file permissions
- Password validation
- SSL/TLS support

✅ **Database Support**
- MariaDB (recommended)
- PostgreSQL
- SQLite (development)

✅ **Production Ready**
- Gunicorn WSGI server
- Nginx reverse proxy
- Redis caching
- Celery task queue
- Systemd service management

## System Requirements

### Minimum Requirements
- **OS**: RHEL/CentOS/Rocky Linux 8+ or Fedora 35+
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB free space
- **Network**: Internet connection for package downloads

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 50+ GB SSD

## Installation Methods

### Method 1: RPM Package (Recommended)

#### Step 1: Build RPM Package

```bash
# Clone repository
git clone https://github.com/htheran/diaken-free.git
cd diaken-free

# Build RPM
./build-rpm.sh
```

#### Step 2: Install RPM

```bash
# Install the package
sudo dnf install ~/rpmbuild/RPMS/noarch/diaken-2.3.6-1.*.noarch.rpm

# Or using rpm directly
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/diaken-2.3.6-1.*.noarch.rpm
```

#### Step 3: Run Interactive Installer

```bash
sudo /usr/local/bin/diaken-install
```

The installer will guide you through:
1. **Database Configuration**
   - Database type selection
   - Database credentials
   - Connection settings

2. **Admin User Setup**
   - Username
   - Email
   - Password (min 8 characters)

3. **Network Configuration**
   - Domain/IP address
   - SSL/TLS option

4. **Installation Confirmation**
   - Review all settings
   - Confirm to proceed

5. **Automated Installation**
   - Install dependencies
   - Configure database
   - Set up Python environment
   - Run migrations
   - Create admin user
   - Configure services
   - Start application

### Method 2: Manual Installation

If you prefer manual installation or need to customize:

```bash
# Clone repository
git clone https://github.com/htheran/diaken-free.git
cd diaken-free

# Run the bash installer
sudo bash install-diaken-rpm.sh
```

## Post-Installation

### Access the Application

```bash
# Default URL
http://YOUR_SERVER_IP

# Or with domain
http://your-domain.com

# With SSL
https://your-domain.com
```

### Service Management

```bash
# Check status
sudo systemctl status diaken
sudo systemctl status diaken-celery
sudo systemctl status diaken-celery-beat

# Restart services
sudo systemctl restart diaken
sudo systemctl restart diaken-celery
sudo systemctl restart diaken-celery-beat

# View logs
sudo journalctl -u diaken -f
sudo journalctl -u diaken-celery -f

# Application logs
sudo tail -f /var/log/diaken/error.log
sudo tail -f /var/log/diaken/access.log
```

### Verify Installation

```bash
# Run verification script
sudo bash /opt/diaken/sc/check_installation.sh
```

This will check:
- Service status
- Log files
- Cron jobs
- Disk usage
- Recent log entries

## Configuration

### Database Configuration

Edit `/opt/diaken/.env`:

```bash
DB_ENGINE=django.db.backends.mysql
DB_NAME=diaken_db
DB_USER=diaken_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

### Nginx Configuration

Edit `/etc/nginx/conf.d/diaken-nginx.conf`

```bash
# Reload nginx after changes
sudo systemctl reload nginx
```

### SSL/TLS Setup

#### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo dnf install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

#### Using Self-Signed Certificate

```bash
# Generate certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/diaken.key \
  -out /etc/nginx/ssl/diaken.crt

# Update nginx config to use SSL
sudo vim /etc/nginx/conf.d/diaken-nginx.conf

# Restart nginx
sudo systemctl restart nginx
```

## Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

## Backup and Restore

### Backup

```bash
# Create backup directory
sudo mkdir -p /backup/diaken

# Backup database (MariaDB)
sudo mysqldump -u root -p diaken_db > /backup/diaken/db_$(date +%Y%m%d).sql

# Backup application files
sudo tar czf /backup/diaken/app_$(date +%Y%m%d).tar.gz /opt/diaken

# Backup configuration
sudo tar czf /backup/diaken/config_$(date +%Y%m%d).tar.gz \
  /etc/nginx/conf.d/diaken-nginx.conf \
  /etc/systemd/system/diaken*.service
```

### Restore

```bash
# Restore database
sudo mysql -u root -p diaken_db < /backup/diaken/db_YYYYMMDD.sql

# Restore application
sudo tar xzf /backup/diaken/app_YYYYMMDD.tar.gz -C /

# Restart services
sudo systemctl restart diaken
```

## Upgrading

```bash
# Stop services
sudo systemctl stop diaken-celery-beat
sudo systemctl stop diaken-celery
sudo systemctl stop diaken

# Backup current installation
sudo tar czf /backup/diaken_pre_upgrade_$(date +%Y%m%d).tar.gz /opt/diaken

# Install new RPM
sudo dnf upgrade diaken-2.3.6-1.*.noarch.rpm

# Run migrations
cd /opt/diaken
source venv/bin/activate
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start services
sudo systemctl start diaken
sudo systemctl start diaken-celery
sudo systemctl start diaken-celery-beat
```

## Uninstallation

```bash
# Stop and disable services
sudo systemctl stop diaken-celery-beat diaken-celery diaken
sudo systemctl disable diaken-celery-beat diaken-celery diaken

# Remove RPM package
sudo dnf remove diaken

# Remove data (optional)
sudo rm -rf /opt/diaken
sudo rm -rf /var/log/diaken
sudo userdel -r diaken
```

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status diaken

# Check logs
sudo journalctl -u diaken -n 50

# Check application logs
sudo tail -100 /var/log/diaken/error.log
```

### Database connection errors

```bash
# Test database connection
cd /opt/diaken
source venv/bin/activate
python manage.py dbshell

# Check database service
sudo systemctl status mariadb
```

### Permission errors

```bash
# Fix permissions
sudo chown -R diaken:diaken /opt/diaken
sudo chown -R diaken:diaken /var/log/diaken
sudo chmod -R 755 /opt/diaken
```

### Nginx errors

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/diaken_error.log

# Restart nginx
sudo systemctl restart nginx
```

## Security Best Practices

1. **Change default passwords** immediately after installation
2. **Enable SSL/TLS** for production deployments
3. **Configure firewall** to allow only necessary ports
4. **Regular backups** of database and application files
5. **Keep system updated** with security patches
6. **Monitor logs** for suspicious activity
7. **Use strong passwords** (min 12 characters, mixed case, numbers, symbols)
8. **Restrict SSH access** to specific IPs if possible
9. **Enable SELinux** in enforcing mode
10. **Regular security audits**

## Support

- **Documentation**: https://github.com/htheran/diaken-free
- **Issues**: https://github.com/htheran/diaken-free/issues
- **Email**: support@diaken.io

## License

Proprietary - See LICENSE file for details
