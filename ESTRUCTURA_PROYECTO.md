# 📁 Estructura del Proyecto Diaken

## 🎯 Estructura de Directorios

### Organización de Playbooks y Scripts

```
diaken/
├── media/                          # Directorio de archivos del usuario
│   ├── playbooks/                  # Playbooks de Ansible
│   │   ├── windows/               # Playbooks para Windows
│   │   │   ├── host/              # Ejecutar en hosts individuales
│   │   │   └── group/             # Ejecutar en grupos
│   │   ├── redhat/                # Playbooks para RedHat/CentOS/Oracle
│   │   │   ├── host/
│   │   │   └── group/
│   │   └── debian/                # Playbooks para Debian/Ubuntu
│   │       ├── host/
│   │       └── group/
│   │
│   └── scripts/                   # Scripts de sistema
│       ├── powershell/            # Scripts PowerShell (Windows)
│       │   ├── host/
│       │   └── group/
│       ├── redhat/                # Scripts Bash (RedHat)
│       │   ├── host/
│       │   └── group/
│       └── debian/                # Scripts Bash (Debian)
│           ├── host/
│           └── group/
│
├── logs/                          # Logs de la aplicación (creado automáticamente)
├── db.sqlite3                     # Base de datos SQLite (desarrollo)
└── manage.py
```

## 🔧 Configuración de Rutas

### Rutas Absolutas (No Relativas)

Todas las rutas se calculan dinámicamente usando `BASE_DIR`:

```python
# settings.py
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(str(BASE_DIR), 'media')

# Estructura:
# media/
#   playbooks/{os_family}/{target_type}/{filename}
#   scripts/{os_family}/{target_type}/{filename}
```

### Ventajas de Rutas Absolutas

✅ **Portable**: Funciona en cualquier directorio
✅ **Sin hardcoding**: No hay rutas fijas como `/opt/www/app`
✅ **Independiente del usuario**: Funciona con cualquier usuario del sistema
✅ **Auto-creación**: Los directorios se crean automáticamente al guardar

## 📊 Modelos de Datos

### Playbook Model

```python
class Playbook(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    playbook_type = models.CharField(
        max_length=10,
        choices=[('host', 'Host'), ('group', 'Group')]
    )
    os_family = models.CharField(
        max_length=10,
        choices=[
            ('redhat', 'RedHat/CentOS'),
            ('debian', 'Debian/Ubuntu'),
            ('windows', 'Windows'),
        ]
    )
    file = models.FileField(upload_to=playbook_upload_path)
```

**Ruta generada**: `playbooks/{os_family}/{playbook_type}/{filename}`

**Ejemplo**: `playbooks/windows/host/Update-Windows-Host.yml`

### Script Model

```python
class Script(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_type = models.CharField(
        max_length=10,
        choices=[('host', 'Host'), ('group', 'Group')]
    )
    os_family = models.CharField(
        max_length=20,
        choices=[
            ('redhat', 'RedHat/CentOS/Oracle Linux'),
            ('debian', 'Debian/Ubuntu'),
            ('windows', 'Windows'),
        ]
    )
    file_path = models.CharField(max_length=500)  # Ruta absoluta
```

**Ruta generada**: `scripts/{os_dir}/{target_type}/{name}.{ext}`
- Windows → `powershell/` con extensión `.ps1`
- Linux → `redhat/` o `debian/` con extensión `.sh`

## 🗄️ Ubicación de Archivos: App vs Base de Datos

### ✅ Recomendación: Guardar con la Aplicación

**Los playbooks y scripts SIEMPRE deben estar con la aplicación, NO con la base de datos.**

```
Servidor de Aplicación              Servidor de Base de Datos
┌─────────────────────────┐        ┌──────────────────────┐
│ /var/www/diaken/        │        │ PostgreSQL/MySQL     │
│ ├── manage.py           │        │                      │
│ ├── media/              │ ←─     │ Solo metadata:       │
│ │   ├── playbooks/      │   │    │ - Nombres            │
│ │   └── scripts/        │   │    │ - Descripciones      │
│ └── logs/               │   │    │ - Rutas relativas    │
│                         │   │    │ - Configuración      │
│ Archivos físicos AQUÍ   │   └────│ NO archivos físicos  │
└─────────────────────────┘        └──────────────────────┘
```

### Razones Técnicas:

1. **Performance**: Acceso directo sin latencia de red
2. **Confiabilidad**: No depende de conexión a BD
3. **Simplicidad**: Un solo punto de backup
4. **Velocidad**: Ansible ejecuta archivos locales directamente
5. **Estándar Django**: MEDIA_ROOT debe estar con la app

## 🚀 Instalación en Cualquier Máquina

### Desarrollo

```bash
# Clonar en CUALQUIER directorio
git clone git@github.com:htheran/diaken-free.git /mi/ruta/elegida/diaken
cd /mi/ruta/elegida/diaken

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Migrar base de datos
python manage.py migrate

# Crear directorios (automático al usar la app)
# Se crean en: /mi/ruta/elegida/diaken/media/

# Ejecutar servidor
python manage.py runserver 0.0.0.0:9090
```

### Producción

```bash
# Crear usuario (OPCIONAL - cualquier nombre)
sudo useradd -m -s /bin/bash miapp

# Clonar en cualquier ubicación
sudo -u miapp git clone git@github.com:htheran/diaken-free.git /srv/apps/diaken
cd /srv/apps/diaken

# ... resto del setup ...
```

## 📝 Migración de Archivos Existentes

Si tienes archivos en la estructura antigua, usa el script de migración:

```bash
python scripts/migrate_playbooks_structure.py
```

Este script:
- ✅ Detecta el SO automáticamente por el nombre del archivo
- ✅ Mueve los archivos a la estructura correcta
- ✅ Actualiza la base de datos
- ✅ Identifica archivos huérfanos

## 🔒 Permisos

Los directorios se crean automáticamente con permisos del usuario que ejecuta la app.

**No se requiere usuario específico "diaken"**. Funciona con cualquier usuario.

## 📦 Backup

Para hacer backup completo:

```bash
# Backup de todo (código + datos + archivos)
tar -czf diaken-backup-$(date +%Y%m%d).tar.gz \
    /ruta/a/diaken/ \
    --exclude=venv \
    --exclude=__pycache__
```

El backup incluye:
- Código fuente
- Base de datos (db.sqlite3)
- Media (playbooks y scripts)
- Logs

## ✨ Ventajas de la Nueva Estructura

1. ✅ **Organización clara** por Sistema Operativo
2. ✅ **Escalable** - fácil agregar nuevos OS
3. ✅ **Portable** - funciona en cualquier directorio
4. ✅ **Auto-mantenida** - directorios se crean automáticamente
5. ✅ **Sin configuración** - no requiere variables de entorno
6. ✅ **Independiente de usuario** - funciona con cualquier usuario
7. ✅ **Siguiendo estándares** - estructura lógica y predecible
