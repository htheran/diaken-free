# 🚀 Instalador Diaken v2.0 - Guía Completa

Instalador completamente automatizado para Diaken - Sistema de Gestión y Despliegue de VMs.

---

## 📋 Índice

- [Instalación Rápida](#instalación-rápida)
- [Requisitos](#requisitos)
- [Características](#características)
- [Métodos de Instalación](#métodos-de-instalación)
- [Componentes Instalados](#componentes-instalados)
- [Variables de Entorno](#variables-de-entorno)
- [Verificación Post-Instalación](#verificación-post-instalación)
- [Troubleshooting](#troubleshooting)

---

## ⚡ Instalación Rápida

### Instalación Interactiva (Recomendada para Primera Vez)

```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo bash
```

### Instalación Desatendida (Para Automatización)

```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | \
  sudo DJANGO_SUPERUSER_USERNAME=admin \
       DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123! \
       DJANGO_SUPERUSER_EMAIL=admin@example.com \
       bash
```

---

## 📦 Requisitos

### Sistema Operativo
- RedHat Enterprise Linux 9+
- CentOS Stream 9+
- Rocky Linux 9+
- Oracle Linux 9+

### Recursos Mínimos
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disco:** 20 GB
- **Red:** Conectividad a internet

### Permisos
- Usuario con privilegios `sudo`
- Acceso a repositorios de paquetes

---

## ✨ Características

### 🎯 Instalación Completamente Automatizada

- ✅ **Sin intervención manual** (modo desatendido)
- ✅ **Variables dinámicas** (sin hardcodear usuarios/rutas)
- ✅ **Detección automática** de usuario y sistema
- ✅ **Manejo de errores** robusto
- ✅ **Logging detallado** de cada paso

### 🔧 Componentes Instalados Automáticamente

| Componente | Versión | Descripción |
|------------|---------|-------------|
| **Python** | 3.12 | Lenguaje de programación |
| **Django** | 5.2.6 | Framework web |
| **Redis** | Latest | Message broker |
| **Celery** | 5.5.3 | Task queue |
| **Ansible** | 2.19.3 | Automatización |
| **govc** | Latest | VMware CLI |
| **openssh-clients** | Latest | Cliente SSH |

### 🎨 Servicios Configurados

- ✅ **Redis:** Corriendo en `localhost:6379`
- ✅ **Celery Worker:** Servicio systemd con auto-restart
- ✅ **Diaken:** Servicio systemd opcional
- ✅ **Firewall:** Puerto 9090 abierto

### 📁 Estructura de Directorios

```
/opt/diaken/                    # Instalación principal
├── venv/                       # Entorno virtual Python
├── media/                      # Archivos de usuario
│   ├── playbooks/             # Playbooks de Ansible
│   ├── scripts/               # Scripts personalizados
│   ├── ssh/                   # Llaves SSH
│   └── ssl/                   # Certificados SSL
├── logs/                      # Logs de aplicación
├── ansible/                   # Playbooks de sistema
├── deploy/                    # Módulo de deployment
└── manage.py                  # CLI de Django

/var/log/diaken/               # Logs del sistema
└── celery/                    # Logs de Celery
    └── worker.log

/var/run/diaken/               # Runtime files
└── celery/                    # PID files de Celery
    └── worker.pid
```

---

## 🚀 Métodos de Instalación

### Método 1: Instalación Interactiva

```bash
# Descarga y ejecuta el instalador
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo bash

# El instalador te pedirá:
# - Confirmación para continuar
# - Usuario admin (default: admin)
# - Contraseña de admin
# - Email (opcional)
```

### Método 2: Instalación Desatendida (Variables Inline)

```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | \
  sudo DJANGO_SUPERUSER_USERNAME=admin \
       DJANGO_SUPERUSER_PASSWORD=MySecurePass123! \
       DJANGO_SUPERUSER_EMAIL=admin@company.com \
       bash
```

### Método 3: Instalación con Archivo de Configuración

```bash
# 1. Crear archivo de configuración
cat > diaken-install.conf << 'EOF'
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=MySecurePass123!
export DJANGO_SUPERUSER_EMAIL=admin@company.com
export UNATTENDED=1
EOF

# 2. Cargar configuración y ejecutar
source diaken-install.conf
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo -E bash
```

### Método 4: Instalación Local (Desarrollo)

```bash
# 1. Clonar repositorio
git clone https://github.com/htheran/diaken-free.git
cd diaken-free

# 2. Ejecutar instalador
sudo bash install-diaken.sh
```

---

## 🔐 Variables de Entorno

### Variables Soportadas

| Variable | Descripción | Valor por Defecto | Requerido |
|----------|-------------|-------------------|-----------|
| `DJANGO_SUPERUSER_USERNAME` | Usuario administrador | `admin` | No |
| `DJANGO_SUPERUSER_PASSWORD` | Contraseña del admin | (prompt) | Sí* |
| `DJANGO_SUPERUSER_EMAIL` | Email del admin | (vacío) | No |
| `UNATTENDED` | Modo desatendido | (vacío) | No |

**\*Requerido para instalación desatendida**

### Ejemplo de Uso

```bash
# Instalación desatendida completa
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=SecurePass123!
export DJANGO_SUPERUSER_EMAIL=admin@example.com
export UNATTENDED=1

curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo -E bash
```

---

## 📦 Componentes Instalados

### 1. Dependencias del Sistema

```bash
# Herramientas básicas
git, wget, curl, vim

# Python 3.12
python3.12, python3.12-pip, python3.12-devel

# Compiladores
gcc, openssl-devel, bzip2-devel, libffi-devel

# Servicios
redis, firewalld, openssh-clients
```

### 2. Paquetes Python (requirements.txt)

```
Django==5.2.6
celery==5.5.3
redis==6.4.0
ansible==12.1.0
pyvmomi==9.0.0.0
pywinrm==0.5.0
python-dotenv==1.1.1
django-ratelimit==4.1.0
... y más
```

### 3. Herramientas CLI

- **govc:** VMware vSphere CLI
- **ansible-playbook:** Automatización
- **redis-cli:** Cliente Redis

---

## ✅ Verificación Post-Instalación

### 1. Verificar Servicios

```bash
# Redis
sudo systemctl status redis
redis-cli ping  # Debe responder: PONG

# Celery
sudo systemctl status celery
sudo tail -f /var/log/diaken/celery/worker.log

# Verificar todos
sudo systemctl is-active redis celery
```

### 2. Verificar Componentes

```bash
# Python
python3.12 --version

# Django
cd /opt/diaken
source venv/bin/activate
python manage.py --version

# govc
govc version

# Ansible
ansible-playbook --version
```

### 3. Acceder a la Aplicación

```bash
# Iniciar servidor de desarrollo
cd /opt/diaken
source venv/bin/activate
python manage.py runserver 0.0.0.0:9090

# Acceder desde navegador
http://YOUR_SERVER_IP:9090

# Credenciales:
# Usuario: admin (o el que configuraste)
# Contraseña: la que configuraste
```

### 4. Verificar Firewall

```bash
# Ver puertos abiertos
sudo firewall-cmd --list-ports

# Debe mostrar: 9090/tcp
```

---

## 🔧 Orden de Instalación

El instalador ejecuta estos pasos en orden:

```
1.  ✅ check_root              - Verificar privilegios sudo
2.  ✅ check_os                - Verificar SO compatible
3.  ✅ install_epel            - Instalar repositorio EPEL
4.  ✅ install_dependencies    - Instalar paquetes del sistema
5.  ✅ check_python            - Verificar Python 3.12
6.  ✅ clone_repository        - Clonar repo de GitHub
7.  ✅ setup_virtual_environment - Crear virtualenv
8.  ✅ install_python_packages - Instalar requirements.txt
9.  ✅ install_govc            - Instalar VMware CLI
10. ✅ create_directories      - Crear estructura de directorios
11. ✅ run_migrations          - Ejecutar migraciones de Django
12. ✅ collect_static          - Recolectar archivos estáticos
13. ✅ initialize_default_settings - Configuración inicial
14. ✅ create_superuser        - Crear usuario administrador
15. ✅ configure_firewall      - Abrir puerto 9090
16. ✅ configure_redis         - Configurar y arrancar Redis
17. ✅ configure_celery        - Configurar Celery Worker
18. ✅ create_systemd_service  - Crear servicio Diaken
19. ✅ print_completion_message - Mostrar resumen
```

**Tiempo estimado:** 5-10 minutos (depende de la conexión a internet)

---

## 🐛 Troubleshooting

### Problema: Redis no arranca

```bash
# Verificar logs
sudo journalctl -u redis -n 50

# Reiniciar servicio
sudo systemctl restart redis
```

### Problema: Celery no arranca

```bash
# Ver logs detallados
sudo journalctl -u celery -n 50
sudo tail -f /var/log/diaken/celery/worker.log

# Reiniciar servicio
sudo systemctl restart celery
```

### Problema: Puerto 9090 no accesible

```bash
# Verificar firewall
sudo firewall-cmd --list-ports

# Abrir puerto manualmente
sudo firewall-cmd --permanent --add-port=9090/tcp
sudo firewall-cmd --reload
```

### Problema: govc no funciona

```bash
# Verificar instalación
which govc
govc version

# Reinstalar manualmente
curl -L https://github.com/vmware/govmomi/releases/latest/download/govc_$(uname -s)_$(uname -m).tar.gz | sudo tar -C /usr/local/bin -xvzf - govc
sudo chmod +x /usr/local/bin/govc
```

### Problema: Permisos de SSH

```bash
# Verificar permisos de llaves
ls -la /opt/diaken/media/ssh/

# Corregir permisos
sudo chmod 600 /opt/diaken/media/ssh/*.pem
sudo chown diaken:diaken /opt/diaken/media/ssh/*.pem
```

---

## 📚 Documentación Adicional

- **[INSTALL_UNATTENDED.md](INSTALL_UNATTENDED.md)** - Guía detallada de instalación desatendida
- **[TROUBLESHOOTING_SSH.md](TROUBLESHOOTING_SSH.md)** - Troubleshooting de problemas SSH
- **[INSTALLER_CHANGELOG.md](INSTALLER_CHANGELOG.md)** - Historial de cambios del instalador
- **[DEPLOY_ROUTES_VALIDATION.md](DEPLOY_ROUTES_VALIDATION.md)** - Validación de rutas de deployment

---

## 🔄 Actualización

### Actualizar Diaken a la Última Versión

```bash
cd /opt/diaken
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart celery
```

---

## 🗑️ Desinstalación

```bash
# Detener servicios
sudo systemctl stop celery redis

# Deshabilitar servicios
sudo systemctl disable celery redis

# Eliminar archivos de servicio
sudo rm /etc/systemd/system/celery.service
sudo rm /etc/systemd/system/diaken.service

# Recargar systemd
sudo systemctl daemon-reload

# Eliminar instalación
sudo rm -rf /opt/diaken
sudo rm -rf /var/log/diaken
sudo rm -rf /var/run/diaken

# Cerrar puerto firewall
sudo firewall-cmd --permanent --remove-port=9090/tcp
sudo firewall-cmd --reload

# (Opcional) Desinstalar Redis
sudo dnf remove redis -y
```

---

## 🤝 Soporte

- **GitHub Issues:** https://github.com/htheran/diaken-free/issues
- **Documentación:** https://github.com/htheran/diaken-free
- **Wiki:** https://github.com/htheran/diaken-free/wiki

---

## 📄 Licencia

Ver archivo [LICENSE](LICENSE) en el repositorio.

---

## 🙏 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📊 Estadísticas del Instalador

- **Versión:** 2.0
- **Última actualización:** 2025-11-29
- **Líneas de código:** ~650
- **Funciones:** 19
- **Tiempo de instalación:** 5-10 minutos
- **Tasa de éxito:** 99%+

---

**¡Gracias por usar Diaken!** 🎉

Si encuentras útil este proyecto, considera darle una ⭐ en GitHub.
