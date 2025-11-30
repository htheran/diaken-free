# 📦 Componentes de Diaken - Inventario Completo

Listado completo de todos los componentes, dependencias y servicios instalados por Diaken.

---

## 🐍 Python & Django

### Core Framework
```
Python: 3.12.11
Django: 5.2.6
```

### Dependencias Python (requirements.txt)

#### Framework Web
- `Django==5.2.6` - Framework web principal
- `asgiref==3.9.2` - ASGI server
- `sqlparse==0.5.3` - SQL parser
- `tzdata==2025.2` - Timezone data

#### Task Queue & Messaging
- `celery==5.5.3` - Distributed task queue
- `redis==6.4.0` - Redis client
- `kombu==5.5.4` - Messaging library
- `amqp==5.3.1` - AMQP protocol
- `billiard==4.2.2` - Process pool
- `vine==5.1.0` - Promises/futures

#### Automatización (Ansible)
- `ansible==12.1.0` - Automation platform
- `ansible-core==2.19.3` - Ansible core
- `Jinja2==3.1.6` - Template engine
- `MarkupSafe==3.0.3` - String escaping
- `PyYAML==6.0.3` - YAML parser
- `resolvelib==1.2.1` - Dependency resolver
- `packaging==25.0` - Package utilities

#### VMware Integration
- `pyvmomi==9.0.0.0` - VMware vSphere API
- `pywinrm==0.5.0` - Windows Remote Management

#### Security & Crypto
- `cryptography==46.0.2` - Cryptographic recipes
- `cffi==2.0.0` - C Foreign Function Interface
- `pycparser==2.23` - C parser
- `pyspnego==0.12.0` - SPNEGO authentication
- `requests-credssp==2.0.0` - CredSSP authentication
- `requests_ntlm==1.3.0` - NTLM authentication

#### HTTP & Networking
- `requests==2.32.5` - HTTP library
- `urllib3==2.5.0` - HTTP client
- `certifi==2025.10.5` - CA certificates
- `charset-normalizer==3.4.3` - Character encoding
- `idna==3.10` - Internationalized domain names

#### Utilities
- `python-dotenv==1.1.1` - Environment variables
- `python-dateutil==2.9.0.post0` - Date utilities
- `pytz==2025.2` - Timezone definitions
- `six==1.17.0` - Python 2/3 compatibility
- `typing_extensions==4.15.0` - Type hints
- `xmltodict==1.0.2` - XML to dict converter

#### CLI & Interactive
- `click==8.3.0` - CLI framework
- `click-didyoumean==0.3.1` - Command suggestions
- `click-plugins==1.1.1.2` - Click plugins
- `click-repl==0.3.0` - REPL for Click
- `prompt_toolkit==3.0.52` - Interactive prompts
- `wcwidth==0.2.14` - Terminal width

#### Security & Rate Limiting
- `django-ratelimit==4.1.0` - Rate limiting for Django

---

## 🔧 Servicios del Sistema

### Redis
```
Servicio: redis.service
Puerto: 6379
Configuración: /etc/redis/redis.conf
Logs: journalctl -u redis
Estado: systemctl status redis
```

**Uso:**
- Message broker para Celery
- Backend de resultados para Celery
- Cache (opcional)

### Celery Worker
```
Servicio: celery.service
Tipo: forking
Workers: 3 (por defecto)
Logs: /var/log/diaken/celery/worker.log
PID: /var/run/diaken/celery/worker.pid
Estado: systemctl status celery
```

**Configuración:**
```ini
[Service]
Type=forking
User=diaken (dinámico)
WorkingDirectory=/opt/diaken
Environment="PATH=/opt/diaken/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/diaken/venv/bin/celery -A diaken worker --loglevel=info --detach
Restart=always
RestartSec=10s
```

### Diaken (Opcional)
```
Servicio: diaken.service
Puerto: 9090
Tipo: simple
Estado: systemctl status diaken
```

**Nota:** El servicio Diaken es opcional. Para desarrollo, usar `python manage.py runserver`.

---

## 🛠️ Herramientas CLI

### govc (VMware CLI)
```
Versión: 0.52.0
Ubicación: /usr/local/bin/govc
Repositorio: https://github.com/vmware/govmomi
```

**Uso:**
```bash
# Configurar credenciales
export GOVC_URL=vcenter.example.com
export GOVC_USERNAME=administrator@vsphere.local
export GOVC_PASSWORD=password
export GOVC_INSECURE=true

# Ejemplos
govc ls
govc vm.info VM_NAME
govc vm.network.change -vm VM_NAME -net "New Network"
```

### Ansible
```
Versión: 2.19.3
Ubicación: /opt/diaken/venv/bin/ansible-playbook
Configuración: /etc/ansible/ansible.cfg
```

**Playbooks incluidos:**
- `/opt/diaken/ansible/provision_vm.yml` - RedHat/CentOS
- `/opt/diaken/ansible/provision_debian_vm.yml` - Debian/Ubuntu

### SSH Client
```
Paquete: openssh-clients
Versión: 8.7p1
Comandos: ssh, scp, sftp, ssh-keygen
```

---

## 🔥 Firewall

### Configuración
```bash
# Servicio
sudo systemctl status firewalld

# Puertos abiertos
sudo firewall-cmd --list-ports
# Resultado: 9090/tcp

# Zonas
sudo firewall-cmd --get-active-zones
```

---

## 📁 Estructura de Archivos

### Directorio Principal: `/opt/diaken`

```
/opt/diaken/
├── ansible/                    # Playbooks de sistema
│   ├── provision_vm.yml
│   └── provision_debian_vm.yml
├── deploy/                     # Módulo de deployment
│   ├── models.py
│   ├── views.py
│   ├── tasks.py               # Tareas de Celery
│   └── ...
├── diaken/                     # Configuración Django
│   ├── settings.py
│   ├── settings_production.py
│   ├── celery.py
│   └── ...
├── media/                      # Archivos de usuario
│   ├── playbooks/             # Playbooks personalizados
│   │   ├── redhat/
│   │   ├── debian/
│   │   └── windows/
│   ├── scripts/               # Scripts personalizados
│   ├── ssh/                   # Llaves SSH privadas
│   └── ssl/                   # Certificados SSL
├── logs/                      # Logs de aplicación
├── static/                    # Archivos estáticos
├── templates/                 # Templates HTML
├── venv/                      # Entorno virtual Python
├── db.sqlite3                 # Base de datos SQLite
├── manage.py                  # CLI de Django
├── requirements.txt           # Dependencias Python
└── install-diaken.sh          # Instalador
```

### Logs del Sistema: `/var/log/diaken`

```
/var/log/diaken/
└── celery/
    └── worker.log             # Logs de Celery Worker
```

### Runtime Files: `/var/run/diaken`

```
/var/run/diaken/
└── celery/
    └── worker.pid             # PID de Celery Worker
```

---

## 🔐 Seguridad

### Permisos de Archivos

```bash
# Llaves SSH
/opt/diaken/media/ssh/*.pem: 600 (rw-------)
/opt/diaken/media/ssh/: 700 (rwx------)

# Directorio principal
/opt/diaken/: 755 (rwxr-xr-x)

# Media y logs
/opt/diaken/media/: 755 (rwxr-xr-x)
/opt/diaken/logs/: 755 (rwxr-xr-x)

# Logs del sistema
/var/log/diaken/: 755 (rwxr-xr-x)
/var/run/diaken/: 755 (rwxr-xr-x)
```

### Ownership

```bash
# Archivos de aplicación
Owner: diaken:diaken (usuario que ejecutó instalación)

# Servicios systemd
Owner: root:root
```

---

## 🌐 Puertos y Servicios

| Puerto | Servicio | Protocolo | Descripción |
|--------|----------|-----------|-------------|
| 9090 | Diaken | TCP | Interfaz web |
| 6379 | Redis | TCP | Message broker (localhost only) |
| 22 | SSH | TCP | Conexión a VMs remotas |

---

## 📊 Recursos del Sistema

### Uso Estimado

| Componente | CPU | RAM | Disco |
|------------|-----|-----|-------|
| Django | ~5% | ~200 MB | ~500 MB |
| Redis | ~1% | ~50 MB | ~100 MB |
| Celery (3 workers) | ~10% | ~400 MB | ~50 MB |
| **Total** | **~16%** | **~650 MB** | **~650 MB** |

**Nota:** Valores aproximados en sistema con 2 CPU cores y 4 GB RAM.

---

## 🔄 Procesos en Ejecución

```bash
# Ver procesos de Diaken
ps aux | grep -E "celery|redis|diaken"

# Resultado esperado:
redis      1234  ... /usr/bin/redis-server 127.0.0.1:6379
diaken     5678  ... python3 -m celery -A diaken worker
diaken     5679  ... python3 -m celery -A diaken worker
diaken     5680  ... python3 -m celery -A diaken worker
```

---

## 📝 Archivos de Configuración

### Django Settings

```python
# /opt/diaken/diaken/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

ANSIBLE_PLAYBOOK_PATH = '/opt/diaken/venv/bin/ansible-playbook'
```

### Celery Configuration

```python
# /opt/diaken/diaken/celery.py
app = Celery('diaken')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### Ansible Configuration

```ini
# /etc/ansible/ansible.cfg
[defaults]
host_key_checking = False
```

---

## 🧪 Comandos de Verificación

```bash
# Verificar todos los componentes
cd /opt/diaken
source venv/bin/activate

# Python
python --version

# Django
python manage.py --version

# Celery
celery -A diaken status

# Redis
redis-cli ping

# govc
govc version

# Ansible
ansible-playbook --version

# Servicios
sudo systemctl is-active redis celery

# Firewall
sudo firewall-cmd --list-ports
```

---

## 📚 Referencias

- **Django:** https://docs.djangoproject.com/
- **Celery:** https://docs.celeryproject.org/
- **Redis:** https://redis.io/documentation
- **Ansible:** https://docs.ansible.com/
- **govc:** https://github.com/vmware/govmomi/tree/main/govc
- **pyvmomi:** https://github.com/vmware/pyvmomi

---

**Última actualización:** 2025-11-29  
**Versión de Diaken:** 2.0  
**Versión del Instalador:** 2.0
