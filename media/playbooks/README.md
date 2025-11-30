# Playbooks de Ansible - Diaken

Esta carpeta contiene los playbooks de Ansible organizados por sistema operativo.

## Estructura de Directorios

```
playbooks/
├── redhat/
│   ├── host/      # Playbooks para hosts individuales RedHat/CentOS/Rocky
│   └── group/     # Playbooks para grupos de hosts RedHat
├── debian/
│   ├── host/      # Playbooks para hosts individuales Debian/Ubuntu
│   └── group/     # Playbooks para grupos de hosts Debian
└── windows/
    ├── host/      # Playbooks para hosts individuales Windows
    └── group/     # Playbooks para grupos de hosts Windows
```

## Uso

### Playbooks de Host
Los playbooks en las carpetas `host/` se ejecutan contra hosts individuales después del deployment.

### Playbooks de Group
Los playbooks en las carpetas `group/` se ejecutan contra grupos de hosts definidos en el inventario.

## Convención de Nombres

- **Host playbooks:** `Action-Target-Host.yml`
  - Ejemplo: `Install-Httpd-Host.yml`
  
- **Group playbooks:** `Action-Target-Group.yml`
  - Ejemplo: `Configure-WebServers-Group.yml`

## Sistemas Operativos Soportados

- **RedHat:** RedHat Enterprise Linux, CentOS, Rocky Linux, AlmaLinux
- **Debian:** Debian, Ubuntu
- **Windows:** Windows Server 2016+, Windows 10+

## Logs

Los logs de ejecución de playbooks se guardan en:
- `/var/log/diaken/ansible/`
