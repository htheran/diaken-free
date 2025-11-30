# Scripts - Diaken

Esta carpeta contiene scripts organizados por sistema operativo.

## Estructura de Directorios

```
scripts/
├── redhat/
│   ├── host/      # Scripts para hosts individuales RedHat/CentOS/Rocky
│   └── group/     # Scripts para grupos de hosts RedHat
├── debian/
│   ├── host/      # Scripts para hosts individuales Debian/Ubuntu
│   └── group/     # Scripts para grupos de hosts Debian
└── windows/
    ├── host/      # Scripts para hosts individuales Windows
    └── group/     # Scripts para grupos de hosts Windows
```

## Tipos de Scripts Soportados

### Linux (RedHat/Debian)
- **Bash Scripts:** `.sh`
- **Python Scripts:** `.py`

### Windows
- **PowerShell:** `.ps1`
- **Batch:** `.bat`, `.cmd`
- **Python Scripts:** `.py`

## Uso

### Scripts de Host
Los scripts en las carpetas `host/` se ejecutan contra hosts individuales.

### Scripts de Group
Los scripts en las carpetas `group/` se ejecutan contra grupos de hosts.

## Convención de Nombres

- **Host scripts:** `action_target_host.ext`
  - Ejemplo: `system_info.sh`, `backup_host.ps1`
  
- **Group scripts:** `action_target_group.ext`
  - Ejemplo: `update_webservers.sh`, `restart_services.ps1`

## Sistemas Operativos Soportados

- **RedHat:** RedHat Enterprise Linux, CentOS, Rocky Linux, AlmaLinux
- **Debian:** Debian, Ubuntu
- **Windows:** Windows Server 2016+, Windows 10+

## Nota Importante

⚠️ Los scripts NO se incluyen en el repositorio Git por razones de seguridad.

**¿Por qué?**
- Los scripts pueden contener lógica específica del entorno
- Pueden incluir credenciales o información sensible
- Las rutas en la base de datos no se pueden restaurar
- Cada instalación debe tener sus propios scripts

**Al clonar el repositorio:**
- ✅ Estructura de directorios completa
- ✅ Este archivo README.md
- ✅ Archivos .gitkeep en cada directorio
- ❌ Scripts (.sh, .ps1, .bat, etc.) NO incluidos

**Para agregar scripts:**
1. Subir scripts vía interfaz web de Diaken
2. O copiar manualmente y registrar en la DB vía interfaz

## Logs

Los logs de ejecución de scripts se guardan en:
- `/var/log/diaken/ansible/` (si se ejecutan vía Ansible)
