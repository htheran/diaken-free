# Aprovisionamiento en Diaken - Explicación Completa

## 📋 Índice
- [¿Qué es el Aprovisionamiento?](#qué-es-el-aprovisionamiento)
- [Estructura de Archivos](#estructura-de-archivos)
- [Flujo de Aprovisionamiento](#flujo-de-aprovisionamiento)
- [Clonación del Repositorio](#clonación-del-repositorio)

---

## ¿Qué es el Aprovisionamiento?

El aprovisionamiento en Diaken es el proceso automatizado de configurar VMs después de su creación. Incluye:

1. **Configuración de red** (IP, gateway, DNS)
2. **Configuración de hostname**
3. **Ejecución de playbooks** adicionales personalizados
4. **Reinicio y validación**

---

## Estructura de Archivos

### 📁 Playbooks de Ansible

```
media/playbooks/
├── README.md              # Documentación de playbooks
├── redhat/
│   ├── host/              # Playbooks para hosts individuales RedHat
│   │   ├── .gitkeep       # Mantiene estructura en Git
│   │   └── *.yml          # ← IGNORADOS por .gitignore
│   └── group/             # Playbooks para grupos de hosts RedHat
│       ├── .gitkeep
│       └── *.yml          # ← IGNORADOS por .gitignore
├── debian/
│   ├── host/
│   │   ├── .gitkeep
│   │   └── *.yml          # ← IGNORADOS por .gitignore
│   └── group/
│       ├── .gitkeep
│       └── *.yml          # ← IGNORADOS por .gitignore
└── windows/
    ├── host/
    │   ├── .gitkeep
    │   └── *.yml          # ← IGNORADOS por .gitignore
    └── group/
        ├── .gitkeep
        └── *.yml          # ← IGNORADOS por .gitignore
```

### 📁 Plantillas Jinja2

```
media/j2/
├── host/                  # Plantillas para hosts
│   ├── httpd.conf.j2      # ← SÍ van al repo
│   ├── apache2.conf.j2
│   └── index.html.j2
└── group/                 # Plantillas para grupos
    ├── virtualhost-ssl.conf.j2
    └── virtualhost-http-redirect.conf.j2
```

---

## Flujo de Aprovisionamiento

### 1. Creación de VM en vCenter
```
Usuario → Diaken → vCenter API
   ↓
VM creada con IP temporal
```

### 2. Conexión SSH
```
Diaken → SSH → VM
   ↓
Verificación de acceso
Corrección de permisos de llave (600)
```

### 3. Ejecución de Playbook de Aprovisionamiento
```
Ansible ejecuta:
├── Configuración de red (IP, gateway, DNS)
├── Configuración de hostname
└── Reinicio programado
```

### 4. Cambio de Red en vCenter
```
govc cambia la VM a la red de producción
```

### 5. Registro en Inventario
```
VM registrada en base de datos:
├── Hostname
├── IP
├── Environment
└── Group
```

### 6. Playbooks Adicionales (Opcional)
```
Si existen playbooks configurados:
├── Update-Redhat-Host.yml
├── Install-Httpd-Host.yml
└── Otros playbooks personalizados
```

---

## Clonación del Repositorio

### ¿Qué pasa al clonar el repo?

#### ✅ SE INCLUYEN en el repositorio:

1. **Estructura de directorios**
   ```
   media/playbooks/redhat/host/.gitkeep
   media/playbooks/redhat/group/.gitkeep
   media/playbooks/debian/host/.gitkeep
   media/playbooks/debian/group/.gitkeep
   media/playbooks/windows/host/.gitkeep
   media/playbooks/windows/group/.gitkeep
   ```

2. **Documentación**
   ```
   media/playbooks/README.md
   ```

3. **Plantillas Jinja2** (siempre se incluyen)
   ```
   media/j2/**/*.j2
   ```

#### ❌ NO SE INCLUYEN en el repositorio:

1. **Playbooks personalizados** (ignorados por .gitignore)
   ```
   media/playbooks/**/*.yml
   media/playbooks/**/*.yaml
   ```
   
   **¿Por qué?**
   - Los playbooks contienen lógica específica del entorno
   - Las rutas en la base de datos no se pueden restaurar
   - Cada instalación debe tener sus propios playbooks
   - Evita conflictos entre instalaciones

2. **Base de datos** (db.sqlite3)
   - NO contiene referencia a playbooks al clonar
   - Variables globales se crean con `init_default_settings`

3. **Archivos de logs** (*.log)

4. **Llaves SSH** (*.pem, *.key)

5. **Variables de entorno** (.env)

---

## ¿Cómo restaurar playbooks después de clonar?

### Opción 1: Subir playbooks manualmente

1. Clonar el repositorio
2. Ejecutar instalador
3. Ir a la interfaz web
4. Subir playbooks vía formulario web
5. Diaken crea automáticamente las rutas en la DB

### Opción 2: Copiar playbooks directamente

```bash
# Copiar playbooks al directorio correcto
cp mis-playbooks/*.yml /opt/diaken/media/playbooks/redhat/host/

# Luego subirlos vía interfaz web para registrar en DB
```

### Opción 3: Script de inicialización

Crear un script `init_playbooks.sh`:

```bash
#!/bin/bash
# Copiar playbooks de ejemplo o personalizados
cp -r /ruta/backup/playbooks/* /opt/diaken/media/playbooks/

# Nota: Aún necesitas subirlos vía interfaz para registrar en DB
```

---

## Variables Globales (GlobalSettings)

### ¿Qué pasa con las variables al clonar?

1. **Base de datos vacía** → `db.sqlite3` NO está en el repo
2. **Migraciones** → Crean estructura de tablas
3. **init_default_settings** → Crea variables por defecto:
   - timezone: America/Bogota
   - date_format: Y-m-d H:i:s  
   - language: en

### Variables NO se hardcodean porque:

- ✅ Son específicas de cada instalación
- ✅ El usuario debe configurarlas según su entorno
- ✅ Pueden contener información sensible
- ✅ Se crean automáticamente con valores por defecto

---

## Proceso Completo de Instalación Desde Cero

```bash
# 1. Clonar repositorio
git clone https://github.com/htheran/diaken-free.git
cd diaken-free

# 2. Ejecutar instalador
curl URL | sudo bash

# El instalador automáticamente:
├── Crea estructura de directorios
├── Crea directorios de logs en /var/log/diaken/
├── Ejecuta migraciones
├── Ejecuta init_default_settings (crea variables globales)
├── Crea superusuario
├── Configura servicios (Redis, Celery, Crontab)
└── Recopila archivos estáticos

# 3. Subir playbooks (vía interfaz web)
# 4. Configurar variables globales adicionales (vía interfaz web)
# 5. ¡Listo para deployar VMs!
```

---

## Resumen

| Componente | En Repo | Por Qué |
|------------|---------|---------|
| Estructura playbooks/ | ✅ Sí (.gitkeep) | Mantener directorios |
| README playbooks | ✅ Sí | Documentación |
| Playbooks *.yml | ❌ No | Específicos del entorno |
| Plantillas j2/ | ✅ Sí | Comunes a todas instalaciones |
| Base de datos | ❌ No | Específica de cada instalación |
| Variables globales | ❌ No | Se crean con init_default_settings |
| Logs | ❌ No | Específicos de cada servidor |

---

## Logs Centralizados

Todos los logs se guardan en:

```
/var/log/diaken/
├── celery/
│   └── worker.log
├── django/
│   └── *.log
├── ansible/
│   └── *.log
├── redis/
│   └── redis-server.log
├── cleanup_stuck_deployments.log
└── cleanup_snapshots.log
```

El instalador crea automáticamente esta estructura.

---

## Preguntas Frecuentes

### ¿Por qué no se incluyen los playbooks en el repo?

**Respuesta:** Los playbooks contienen configuraciones específicas del entorno (IPs, rutas, credenciales). Cada instalación debe tener sus propios playbooks. Además, las rutas de playbooks se almacenan en la base de datos, que tampoco está en el repo.

### ¿Cómo migro playbooks entre instalaciones?

**Respuesta:** Exporta los playbooks desde la interfaz web, copia los archivos, e impórtalos en la nueva instalación. Esto actualiza automáticamente las rutas en la base de datos.

### ¿Las plantillas j2 sí van al repo?

**Respuesta:** Sí, las plantillas Jinja2 son comunes a todas las instalaciones y no contienen datos sensibles. Son archivos de configuración genéricos.

---

**Versión:** 2.1.2  
**Fecha:** 2025-11-30
