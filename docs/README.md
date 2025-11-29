# 🚀 Sistema de Despliegue Automatizado de VMs

Sistema profesional de despliegue automatizado de máquinas virtuales con integración completa de vCenter y Ansible.

## 📋 Características

- ✅ Despliegue automatizado de VMs desde vCenter
- ✅ Post-configuración con Ansible
- ✅ Gestión de inventario de hosts
- ✅ Historial completo de despliegues
- ✅ Gestión de playbooks y templates Jinja2
- ✅ Validaciones de duplicados
- ✅ Interfaz web intuitiva

## 🛠️ Requisitos

- Python 3.9+
- Django 5.2.6
- Ansible 2.14+
- vCenter 6.5+
- Oracle Linux 9 / RedHat / CentOS

## 📦 Instalación

```bash
# Clonar repositorio
cd /opt/www/app

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install django pyvmomi

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver 0.0.0.0:8001
```

## ⚙️ Configuración

### 1. Variables Globales
Accede a **Settings → Variables** y configura:

```
[Default]
deploy_env = NEWS
deploy_group = NEWS

[Template Redhat]
ip_template = 10.100.18.80

[Update]
log_dir_update = /var/log/ansible_updates
update_package = *
```

### 2. Credenciales SSH
Accede a **Settings → Credentials** y sube tu llave SSH.

### 3. vCenter
Accede a **Settings → vCenter** y configura:
- Host
- User
- Password

## 🚀 Uso

### Desplegar una VM

1. Ve a **Deploy → Deploy New VM**
2. Completa el formulario:
   - Datacenter
   - Cluster
   - Template
   - Hostname
   - IP Address
   - Operating System
   - Additional Playbook (opcional)
3. Click en **Deploy VM**
4. Monitorea el progreso en el modal
5. Revisa el historial en **History**

### Gestionar Playbooks

1. Ve a **Playbooks → Upload Playbook**
2. Sube tu playbook `.yml`
3. Selecciona el tipo (Host/Group)
4. El playbook estará disponible en el formulario de deploy

### Gestionar Templates Jinja2

1. Ve a **Settings → Ansible Templates**
2. Click en **Upload Template**
3. Sube tu template `.j2`
4. Selecciona el tipo (Host/Group)
5. Usa en tus playbooks: `/opt/www/app/media/j2/host/archivo.j2`

## 📁 Estructura

```
/opt/www/app/
├── deploy/              # Lógica de despliegue
├── inventory/           # Gestión de inventario
├── history/             # Historial de despliegues
├── playbooks/           # Gestión de playbooks
├── settings/            # Configuración global
├── ansible/             # Playbooks de aprovisionamiento
├── media/
│   ├── playbooks/       # Playbooks subidos
│   ├── j2/              # Templates Jinja2
│   │   ├── host/
│   │   └── group/
│   └── ssh/             # Llaves SSH
└── templates/           # Templates HTML
```

## 🔐 Seguridad

- Llaves SSH con permisos 0600
- Validación de formato de llaves
- Validación de duplicados
- StrictHostKeyChecking=no solo para automatización

## 📊 Monitoreo

- Dashboard con estadísticas
- Historial completo de despliegues
- Outputs de Ansible almacenados
- Filtrado por estado y fechas

## 🐛 Troubleshooting

### Error: "Hostname already exists"
El hostname ya está registrado en el inventario. Usa otro nombre.

### Error: "VM already exists in vCenter"
Ya existe una VM con ese nombre en vCenter. Usa otro nombre.

### Error: "recursive loop detected"
Verifica que tus playbooks usen `inventory_hostname` en lugar de `target_host`.

## 📝 Licencia

Propietario - Todos los derechos reservados

## 👥 Autor

Sistema desarrollado para automatización de infraestructura
