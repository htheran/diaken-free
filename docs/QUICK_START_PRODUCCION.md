# 🚀 Quick Start - Deployment a Producción

## Resumen Rápido para Oracle Linux 9.6

---

## ⚡ Opción 1: Script Automatizado (Recomendado)

### 1. Clonar el repositorio en tu servidor de producción

```bash
# Conectar al servidor Oracle Linux 9.6
ssh user@your-server.example.com

# Clonar el proyecto
cd /tmp
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
```

### 2. Editar configuración del script

```bash
nano deploy_production.sh
```

**Cambiar estas líneas:**
```bash
GITHUB_REPO="https://github.com/TU_USUARIO/TU_REPO.git"  # Tu repo de GitHub
SERVER_NAME="your-server.example.com"  # Tu dominio o hostname
SERVER_IP="10.100.x.x"  # IP del servidor
```

### 3. Ejecutar el script

```bash
sudo bash deploy_production.sh
```

El script te pedirá:
- **vCenter URL**: `vcenter.example.com`
- **vCenter Username**: `administrator@vsphere.local`
- **vCenter Password**: `tu_password`

### 4. Crear superusuario de Django

```bash
sudo -u apache /opt/www/diaken/venv/bin/python /opt/www/diaken/manage.py createsuperuser --settings=diaken.settings_production
```

### 5. Acceder a la aplicación

```
http://your-server.example.com/
http://10.100.x.x/
```

---

## 📝 Opción 2: Instalación Manual

Si prefieres hacerlo paso a paso, sigue la guía completa:

```bash
less /opt/www/diaken/DEPLOYMENT_PRODUCCION.md
```

---

## 🔍 Verificación Post-Deployment

### Verificar que Apache está corriendo

```bash
sudo systemctl status httpd
```

### Verificar logs

```bash
# Logs de Apache
sudo tail -f /opt/www/logs/apache_error.log

# Logs de Django
sudo tail -f /opt/www/logs/django.log
```

### Probar la aplicación

```bash
curl http://localhost/
```

### Verificar govc

```bash
sudo -u apache govc about
```

---

## 📂 Estructura de Archivos

```
/opt/www/
├── diaken/                    # Proyecto Django (desde GitHub)
│   ├── manage.py
│   ├── requirements.txt
│   ├── diaken/               # Settings del proyecto
│   │   ├── settings.py
│   │   ├── settings_production.py  ← Creado por script
│   │   └── wsgi.py
│   ├── deploy/               # App de deployment
│   ├── ansible/              # Playbooks de Ansible
│   ├── static/               # Archivos estáticos
│   ├── staticfiles/          # Archivos estáticos recolectados
│   ├── media/                # Archivos subidos (SSH keys)
│   └── venv/                 # Virtual environment
├── logs/                      # Logs de Apache y Django
│   ├── apache_access.log
│   ├── apache_error.log
│   └── django.log
└── backups/                   # Backups de base de datos
    └── db_backup_*.sqlite3
```

---

## 🔧 Comandos Útiles

### Reiniciar Apache

```bash
sudo systemctl restart httpd
```

### Ver logs en tiempo real

```bash
sudo tail -f /opt/www/logs/apache_error.log
sudo tail -f /opt/www/logs/django.log
```

### Actualizar el proyecto

```bash
sudo /opt/www/scripts/update_diaken.sh
```

### Hacer backup de la base de datos

```bash
sudo /opt/www/scripts/backup_db.sh
```

### Recolectar archivos estáticos

```bash
cd /opt/www/diaken
sudo -u apache /opt/www/diaken/venv/bin/python manage.py collectstatic --noinput --settings=diaken.settings_production
```

### Migrar base de datos

```bash
cd /opt/www/diaken
sudo -u apache /opt/www/diaken/venv/bin/python manage.py migrate --settings=diaken.settings_production
```

---

## 🐛 Troubleshooting Rápido

### Apache no inicia

```bash
# Ver logs
sudo journalctl -xeu httpd
sudo tail -f /var/log/httpd/error_log

# Verificar sintaxis
sudo httpd -t
```

### Error 500 en la aplicación

```bash
# Ver logs de Django
sudo tail -f /opt/www/logs/django.log
sudo tail -f /opt/www/logs/apache_error.log

# Verificar permisos
ls -la /opt/www/diaken/db.sqlite3
ls -la /opt/www/diaken/media/
```

### govc no funciona

```bash
# Verificar variables de entorno
sudo systemctl show httpd | grep Environment

# Probar govc manualmente
sudo -u apache govc about
```

### Ansible falla

```bash
# Verificar permisos de SSH keys
ls -la /opt/www/diaken/media/ssh/

# Probar Ansible manualmente
sudo -u apache ansible all -i "10.100.18.80," -m ping -u user_diaken --private-key /opt/www/diaken/media/ssh/2.pem
```

---

## 🔐 Configuración de Seguridad

### Cambiar SECRET_KEY

```bash
# Generar nueva clave
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Editar settings_production.py
sudo nano /opt/www/diaken/diaken/settings_production.py
# Cambiar SECRET_KEY = 'nueva_clave_aqui'

# Reiniciar Apache
sudo systemctl restart httpd
```

### Configurar HTTPS (Opcional)

```bash
# Instalar mod_ssl
sudo dnf install -y mod_ssl

# Editar configuración de Apache
sudo nano /etc/httpd/conf.d/diaken.conf
# Agregar VirtualHost para puerto 443 con certificados SSL

# Reiniciar Apache
sudo systemctl restart httpd
```

---

## 📊 Monitoreo

### Ver uso de recursos

```bash
htop
```

### Ver conexiones activas

```bash
sudo netstat -tulpn | grep httpd
```

### Ver procesos de Apache

```bash
ps aux | grep httpd
```

---

## 📚 Documentación Completa

Para más detalles, consultar:

- **Guía completa de deployment**: `/opt/www/diaken/DEPLOYMENT_PRODUCCION.md`
- **Solución de problemas de red/IP**: `/opt/www/diaken/SOLUCION_CAMBIO_RED_IP.md`
- **Documentación de Django**: https://docs.djangoproject.com/
- **Documentación de Apache**: https://httpd.apache.org/docs/
- **Documentación de govc**: https://github.com/vmware/govmomi/tree/master/govc

---

## ✅ Checklist de Deployment

- [ ] Servidor Oracle Linux 9.6 preparado
- [ ] Script `deploy_production.sh` editado con configuración correcta
- [ ] Script ejecutado exitosamente
- [ ] Superusuario de Django creado
- [ ] Apache corriendo (`systemctl status httpd`)
- [ ] Aplicación accesible desde navegador
- [ ] govc funcionando (`sudo -u apache govc about`)
- [ ] Logs sin errores
- [ ] Deployment de prueba exitoso
- [ ] Backup automático configurado

---

## 🎯 Resultado Esperado

Después del deployment exitoso:

✅ **Aplicación web accesible** en `http://your-server.example.com/`  
✅ **Apache sirviendo Django** con mod_wsgi  
✅ **govc configurado** para cambios de red en vCenter  
✅ **Ansible funcionando** para provisioning de VMs  
✅ **Logs funcionando** en `/opt/www/logs/`  
✅ **Scripts de mantenimiento** listos en `/opt/www/scripts/`  
✅ **Deployment completamente automatizado** de VMs con cambio de red e IP  

---

**Tiempo estimado de deployment**: 10-15 minutos (con script automatizado)  
**Versión**: 1.0  
**Fecha**: 2025-10-16  
**Autor**: htheran
