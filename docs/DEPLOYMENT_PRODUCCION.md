# Guía de Deployment a Producción - Oracle Linux 9.6

## 📋 Información del Proyecto

- **Nombre**: Diaken (VMware Automation Platform)
- **Framework**: Django 5.2.6
- **Python**: 3.9+
- **Web Server**: Apache httpd + mod_wsgi
- **OS**: Oracle Linux 9.6
- **Base de datos**: SQLite (desarrollo) / PostgreSQL o MySQL (producción recomendado)

---

## 🎯 Arquitectura de Producción

```
Internet/Intranet
        ↓
    Apache httpd (Puerto 80/443)
        ↓
    mod_wsgi (WSGI Server)
        ↓
    Django Application
        ↓
    SQLite/PostgreSQL Database
```

---

## 📁 Estructura de Directorios Recomendada

```
/opt/www/
├── diaken/                    # Proyecto Django (desde GitHub)
│   ├── manage.py
│   ├── requirements.txt
│   ├── diaken/               # Settings del proyecto
│   ├── deploy/               # App de deployment
│   ├── inventory/            # App de inventario
│   ├── static/               # Archivos estáticos
│   ├── media/                # Archivos subidos (SSH keys, etc)
│   ├── ansible/              # Playbooks de Ansible
│   └── venv/                 # Virtual environment
├── logs/                      # Logs de Apache y Django
│   ├── apache_access.log
│   ├── apache_error.log
│   └── django.log
└── backups/                   # Backups de base de datos
    └── db_backup_YYYYMMDD.sqlite3
```

---

## 🚀 Paso 1: Preparar el Servidor (Oracle Linux 9.6)

### 1.1 Actualizar el sistema

```bash
sudo dnf update -y
```

### 1.2 Instalar dependencias del sistema

```bash
# Python 3.9+ y herramientas de desarrollo
sudo dnf install -y python3.9 python3.9-devel python3-pip python3-virtualenv

# Apache httpd y mod_wsgi
sudo dnf install -y httpd httpd-devel python3-mod_wsgi

# Git para clonar el repositorio
sudo dnf install -y git

# Herramientas de compilación (para algunas dependencias Python)
sudo dnf install -y gcc gcc-c++ make openssl-devel libffi-devel

# Ansible (para ejecutar playbooks)
sudo dnf install -y ansible

# govc (CLI de VMware) - CRÍTICO para cambios de red
sudo dnf install -y wget
cd /tmp
wget https://github.com/vmware/govmomi/releases/download/v0.37.0/govc_Linux_x86_64.tar.gz
sudo tar -C /usr/local/bin -xzf govc_Linux_x86_64.tar.gz govc
sudo chmod +x /usr/local/bin/govc
govc version  # Verificar instalación
```

### 1.3 Configurar SELinux (Opcional pero recomendado)

```bash
# Opción 1: Modo permisivo (más fácil para desarrollo)
sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config

# Opción 2: Configurar políticas específicas (más seguro)
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_connect_db 1
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/www/diaken/media(/.*)?"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/www/diaken/db.sqlite3"
sudo restorecon -Rv /opt/www/diaken/
```

### 1.4 Configurar Firewall

```bash
# Permitir tráfico HTTP y HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-all
```

---

## 📥 Paso 2: Clonar el Proyecto desde GitHub

### 2.1 Crear estructura de directorios

```bash
sudo mkdir -p /opt/www
sudo mkdir -p /opt/www/logs
sudo mkdir -p /opt/www/backups
```

### 2.2 Clonar el repositorio

```bash
cd /opt/www
sudo git clone https://github.com/TU_USUARIO/TU_REPO.git diaken

# O si ya tienes el repositorio configurado:
sudo git clone git@github.com:TU_USUARIO/TU_REPO.git diaken
```

### 2.3 Configurar permisos

```bash
# Cambiar propietario a apache (usuario de httpd)
sudo chown -R apache:apache /opt/www/diaken

# Permisos específicos
sudo chmod 755 /opt/www/diaken
sudo chmod 755 /opt/www/diaken/manage.py
sudo chmod -R 755 /opt/www/diaken/static
sudo chmod -R 755 /opt/www/diaken/media
sudo chmod -R 755 /opt/www/diaken/ansible
```

---

## 🐍 Paso 3: Configurar Python Virtual Environment

### 3.1 Crear virtual environment

```bash
cd /opt/www/diaken
sudo -u apache python3.9 -m venv venv
```

### 3.2 Activar y actualizar pip

```bash
sudo -u apache /opt/www/diaken/venv/bin/pip install --upgrade pip setuptools wheel
```

### 3.3 Instalar dependencias

```bash
sudo -u apache /opt/www/diaken/venv/bin/pip install -r requirements.txt
```

### 3.4 Instalar gunicorn (alternativa a mod_wsgi)

```bash
# Opcional: Si prefieres usar Gunicorn en lugar de mod_wsgi
sudo -u apache /opt/www/diaken/venv/bin/pip install gunicorn
```

---

## ⚙️ Paso 4: Configurar Django para Producción

### 4.1 Crear archivo de configuración de producción

```bash
sudo -u apache nano /opt/www/diaken/diaken/settings_production.py
```

**Contenido de `settings_production.py`:**

```python
from .settings import *

# SECURITY SETTINGS
DEBUG = False
SECRET_KEY = 'GENERA_UNA_CLAVE_SECRETA_AQUI'  # Usar: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# ALLOWED HOSTS
ALLOWED_HOSTS = [
    'your-server.example.com',
    '10.100.x.x',  # IP del servidor
    'localhost',
    '127.0.0.1',
]

# CSRF TRUSTED ORIGINS (para Django 4.0+)
CSRF_TRUSTED_ORIGINS = [
    'http://your-server.example.com',
    'https://your-server.example.com',
]

# DATABASE (Opcional: Migrar a PostgreSQL)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'diaken_db',
#         'USER': 'diaken_user',
#         'PASSWORD': 'password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# STATIC FILES
STATIC_ROOT = '/opt/www/diaken/staticfiles/'
STATIC_URL = '/static/'

MEDIA_ROOT = '/opt/www/diaken/media/'
MEDIA_URL = '/media/'

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/opt/www/logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# SECURITY HEADERS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Si usas HTTPS:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
```

### 4.2 Generar SECRET_KEY

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
# Copiar el output y pegarlo en settings_production.py
```

### 4.3 Configurar variable de entorno

```bash
# Crear archivo .env (opcional)
sudo -u apache nano /opt/www/diaken/.env
```

**Contenido de `.env`:**

```bash
DJANGO_SETTINGS_MODULE=diaken.settings_production
PYTHONPATH=/opt/www/diaken
```

### 4.4 Recolectar archivos estáticos

```bash
cd /opt/www/diaken
sudo -u apache /opt/www/diaken/venv/bin/python manage.py collectstatic --noinput --settings=diaken.settings_production
```

### 4.5 Migrar base de datos

```bash
sudo -u apache /opt/www/diaken/venv/bin/python manage.py migrate --settings=diaken.settings_production
```

### 4.6 Crear superusuario

```bash
sudo -u apache /opt/www/diaken/venv/bin/python manage.py createsuperuser --settings=diaken.settings_production
```

---

## 🌐 Paso 5: Configurar Apache httpd con mod_wsgi

### 5.1 Crear archivo de configuración de Apache

```bash
sudo nano /etc/httpd/conf.d/diaken.conf
```

**Contenido de `diaken.conf`:**

```apache
<VirtualHost *:80>
    ServerName your-server.example.com
    ServerAlias 10.100.x.x
    ServerAdmin admin@example.com

    # Logs
    ErrorLog /opt/www/logs/apache_error.log
    CustomLog /opt/www/logs/apache_access.log combined

    # Django WSGI
    WSGIDaemonProcess diaken python-home=/opt/www/diaken/venv python-path=/opt/www/diaken
    WSGIProcessGroup diaken
    WSGIScriptAlias / /opt/www/diaken/diaken/wsgi.py

    # Permisos para el directorio del proyecto
    <Directory /opt/www/diaken/diaken>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    # Servir archivos estáticos
    Alias /static /opt/www/diaken/staticfiles
    <Directory /opt/www/diaken/staticfiles>
        Require all granted
        Options -Indexes
    </Directory>

    # Servir archivos media (uploads)
    Alias /media /opt/www/diaken/media
    <Directory /opt/www/diaken/media>
        Require all granted
        Options -Indexes
    </Directory>

    # Configuración de seguridad
    <IfModule mod_headers.c>
        Header always set X-Content-Type-Options "nosniff"
        Header always set X-Frame-Options "DENY"
        Header always set X-XSS-Protection "1; mode=block"
    </IfModule>

    # Límites de timeout (importante para deployments largos)
    Timeout 600
    ProxyTimeout 600
</VirtualHost>

# Si tienes certificado SSL (HTTPS):
# <VirtualHost *:443>
#     ServerName your-server.example.com
#     
#     SSLEngine on
#     SSLCertificateFile /etc/pki/tls/certs/tu-servidor.crt
#     SSLCertificateKeyFile /etc/pki/tls/private/tu-servidor.key
#     SSLCertificateChainFile /etc/pki/tls/certs/ca-bundle.crt
#     
#     # Resto de la configuración igual que arriba...
# </VirtualHost>
```

### 5.2 Modificar wsgi.py para usar settings de producción

```bash
sudo nano /opt/www/diaken/diaken/wsgi.py
```

**Modificar la línea de settings:**

```python
import os
from django.core.wsgi import get_wsgi_application

# Usar settings de producción
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings_production')

application = get_wsgi_application()
```

### 5.3 Verificar configuración de Apache

```bash
sudo httpd -t
# Debe mostrar: Syntax OK
```

### 5.4 Habilitar y reiniciar Apache

```bash
sudo systemctl enable httpd
sudo systemctl restart httpd
sudo systemctl status httpd
```

---

## 🔐 Paso 6: Configurar Variables de Entorno para govc

### 6.1 Crear archivo de configuración para Apache

```bash
sudo nano /etc/systemd/system/httpd.service.d/override.conf
```

**Contenido:**

```ini
[Service]
Environment="GOVC_URL=vcenter.example.com"
Environment="GOVC_USERNAME=administrator@vsphere.local"
Environment="GOVC_PASSWORD=TU_PASSWORD_VCENTER"
Environment="GOVC_INSECURE=true"
```

### 6.2 Recargar systemd y reiniciar Apache

```bash
sudo systemctl daemon-reload
sudo systemctl restart httpd
```

### 6.3 Verificar que govc funciona

```bash
# Como usuario apache
sudo -u apache govc about
# Debe mostrar información de vCenter
```

---

## 📝 Paso 7: Configurar Ansible

### 7.1 Configurar ansible.cfg

```bash
sudo nano /opt/www/diaken/ansible.cfg
```

**Contenido:**

```ini
[defaults]
host_key_checking = False
timeout = 30
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 3600

[ssh_connection]
pipelining = True
```

### 7.2 Verificar permisos de SSH keys

```bash
sudo chmod 600 /opt/www/diaken/media/ssh/*.pem
sudo chown apache:apache /opt/www/diaken/media/ssh/*.pem
```

---

## 🔄 Paso 8: Configurar Servicios Adicionales (Opcional)

### 8.1 Celery para tareas asíncronas (si aplica)

```bash
# Instalar Celery y Redis
sudo -u apache /opt/www/diaken/venv/bin/pip install celery redis

# Instalar Redis server
sudo dnf install -y redis
sudo systemctl enable redis
sudo systemctl start redis
```

**Crear servicio de Celery:**

```bash
sudo nano /etc/systemd/system/celery.service
```

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=apache
Group=apache
EnvironmentFile=/opt/www/diaken/.env
WorkingDirectory=/opt/www/diaken
ExecStart=/opt/www/diaken/venv/bin/celery -A diaken worker --loglevel=info --detach

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable celery
sudo systemctl start celery
```

---

## 🔒 Paso 9: Seguridad Adicional

### 9.1 Configurar permisos restrictivos

```bash
# Base de datos solo lectura/escritura para apache
sudo chmod 660 /opt/www/diaken/db.sqlite3
sudo chown apache:apache /opt/www/diaken/db.sqlite3

# Directorio media
sudo chmod 750 /opt/www/diaken/media
sudo chown -R apache:apache /opt/www/diaken/media

# Logs
sudo chmod 750 /opt/www/logs
sudo chown -R apache:apache /opt/www/logs
```

### 9.2 Configurar fail2ban (opcional)

```bash
sudo dnf install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 🧪 Paso 10: Verificar el Deployment

### 10.1 Verificar que Apache está corriendo

```bash
sudo systemctl status httpd
```

### 10.2 Verificar logs

```bash
# Logs de Apache
sudo tail -f /opt/www/logs/apache_error.log
sudo tail -f /opt/www/logs/apache_access.log

# Logs de Django
sudo tail -f /opt/www/logs/django.log
```

### 10.3 Probar la aplicación

```bash
# Desde el servidor
curl http://localhost/

# Desde tu navegador
http://your-server.example.com/
```

### 10.4 Verificar que govc funciona desde Django

1. Acceder a la aplicación web
2. Ir a Deploy → VM
3. Intentar un deployment de prueba
4. Verificar logs para confirmar que govc ejecuta correctamente

---

## 🔄 Paso 11: Mantenimiento y Actualizaciones

### 11.1 Script de actualización

```bash
sudo nano /opt/www/scripts/update_diaken.sh
```

**Contenido:**

```bash
#!/bin/bash
set -e

echo "🔄 Actualizando Diaken..."

# Cambiar al directorio del proyecto
cd /opt/www/diaken

# Hacer backup de la base de datos
echo "📦 Creando backup de base de datos..."
cp db.sqlite3 /opt/www/backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3

# Pull de cambios desde GitHub
echo "📥 Descargando cambios desde GitHub..."
sudo -u apache git pull origin main

# Actualizar dependencias
echo "📦 Actualizando dependencias Python..."
sudo -u apache /opt/www/diaken/venv/bin/pip install -r requirements.txt --upgrade

# Migrar base de datos
echo "🗄️ Migrando base de datos..."
sudo -u apache /opt/www/diaken/venv/bin/python manage.py migrate --settings=diaken.settings_production

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
sudo -u apache /opt/www/diaken/venv/bin/python manage.py collectstatic --noinput --settings=diaken.settings_production

# Reiniciar Apache
echo "🔄 Reiniciando Apache..."
sudo systemctl restart httpd

echo "✅ Actualización completada!"
```

```bash
sudo chmod +x /opt/www/scripts/update_diaken.sh
```

### 11.2 Backup automático de base de datos

```bash
sudo nano /opt/www/scripts/backup_db.sh
```

**Contenido:**

```bash
#!/bin/bash
BACKUP_DIR="/opt/www/backups"
DB_FILE="/opt/www/diaken/db.sqlite3"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear backup
cp $DB_FILE $BACKUP_DIR/db_backup_$DATE.sqlite3

# Mantener solo los últimos 30 backups
cd $BACKUP_DIR
ls -t db_backup_*.sqlite3 | tail -n +31 | xargs -r rm

echo "✅ Backup creado: db_backup_$DATE.sqlite3"
```

```bash
sudo chmod +x /opt/www/scripts/backup_db.sh
```

**Configurar cron para backup diario:**

```bash
sudo crontab -e
```

```cron
# Backup diario a las 2 AM
0 2 * * * /opt/www/scripts/backup_db.sh >> /opt/www/logs/backup.log 2>&1
```

---

## 📊 Paso 12: Monitoreo (Opcional)

### 12.1 Instalar htop para monitoreo de recursos

```bash
sudo dnf install -y htop
```

### 12.2 Configurar logrotate para logs

```bash
sudo nano /etc/logrotate.d/diaken
```

**Contenido:**

```
/opt/www/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 apache apache
    sharedscripts
    postrotate
        systemctl reload httpd > /dev/null 2>&1 || true
    endscript
}
```

---

## ✅ Checklist Final de Deployment

- [ ] Sistema actualizado (`dnf update`)
- [ ] Python 3.9+ instalado
- [ ] Apache httpd instalado y configurado
- [ ] mod_wsgi instalado
- [ ] govc instalado y funcionando
- [ ] Ansible instalado
- [ ] Proyecto clonado en `/opt/www/diaken`
- [ ] Virtual environment creado
- [ ] Dependencias instaladas (`requirements.txt`)
- [ ] `settings_production.py` configurado
- [ ] SECRET_KEY generado
- [ ] ALLOWED_HOSTS configurado
- [ ] Base de datos migrada
- [ ] Superusuario creado
- [ ] Archivos estáticos recolectados
- [ ] Apache configurado (`/etc/httpd/conf.d/diaken.conf`)
- [ ] Variables de entorno de govc configuradas
- [ ] Permisos correctos (`apache:apache`)
- [ ] SELinux configurado
- [ ] Firewall configurado
- [ ] Apache habilitado y corriendo
- [ ] Aplicación accesible desde navegador
- [ ] Deployment de prueba exitoso
- [ ] Logs funcionando correctamente
- [ ] Backup automático configurado

---

## 🆘 Troubleshooting

### Problema: Apache no inicia

```bash
# Verificar logs
sudo journalctl -xeu httpd
sudo tail -f /var/log/httpd/error_log

# Verificar sintaxis
sudo httpd -t

# Verificar SELinux
sudo ausearch -m avc -ts recent
```

### Problema: Error 500 en la aplicación

```bash
# Verificar logs de Django
sudo tail -f /opt/www/logs/django.log
sudo tail -f /opt/www/logs/apache_error.log

# Verificar permisos
ls -la /opt/www/diaken/db.sqlite3
ls -la /opt/www/diaken/media/
```

### Problema: govc no funciona

```bash
# Verificar variables de entorno
sudo systemctl show httpd | grep Environment

# Probar govc manualmente
sudo -u apache govc about

# Verificar conectividad a vCenter
ping vcenter.example.com
```

### Problema: Ansible falla

```bash
# Verificar permisos de SSH keys
ls -la /opt/www/diaken/media/ssh/

# Probar Ansible manualmente
sudo -u apache ansible all -i "10.100.18.80," -m ping -u user_diaken --private-key /opt/www/diaken/media/ssh/2.pem
```

---

## 📞 Soporte

Para más información, consultar:
- Documentación de Django: https://docs.djangoproject.com/
- Documentación de Apache: https://httpd.apache.org/docs/
- Documentación de govc: https://github.com/vmware/govmomi/tree/master/govc
- Archivo de solución: `/opt/www/diaken/SOLUCION_CAMBIO_RED_IP.md`

---

**Fecha de creación**: 2025-10-16  
**Versión**: 1.0  
**Autor**: htheran  
**Estado**: ✅ LISTO PARA PRODUCCIÓN
