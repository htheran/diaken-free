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

## Playbooks de Ejemplo Incluidos

### RedHat/CentOS/Rocky Linux

**Host Playbooks:**
- `Update-Redhat-Host.yml` - Actualiza paquetes del sistema
- `Install-Httpd-Host.yml` - Instala y configura Apache HTTP Server
- `Install-Vsftpd-Host.yml` - Instala y configura servidor FTP
- `Configure-SSL-Host.yml` - Configura certificados SSL
- `Configure-RemoveOldKernels-Host.yml` - Limpia kernels antiguos
- `Mount-HDD-Host.yml` - Monta discos adicionales

**Group Playbooks:**
- `Update-Redhat-Group.yml` - Actualiza grupo de servidores
- `Configure-SSL-Group.yml` - Configura SSL en grupo

### Debian/Ubuntu

**Host Playbooks:**
- `Update-Debian-Host.yml` - Actualiza paquetes del sistema
- `Install-Apache-Debian-Host.yml` - Instala Apache en Debian

### Windows

**Host Playbooks:**
- `Update-Windows-Host.yml` - Actualiza Windows
- `BasicInfo-Windows-Host.yml` - Obtiene información del sistema

## Crear Playbooks Personalizados

1. Navega a la carpeta correspondiente según el OS y tipo (host/group)
2. Crea tu playbook con la convención de nombres
3. Los playbooks aparecerán automáticamente en la interfaz web
4. Selecciona el playbook al crear un deployment

## Notas Importantes

⚠️ **Los playbooks de ejemplo están incluidos en el repositorio**
⚠️ **Tus playbooks personalizados NO se subirán al repositorio (excluidos por .gitignore)**
⚠️ **Solo los archivos que comienzan con `temp_` son temporales**

## Variables Disponibles

Los playbooks tienen acceso a las siguientes variables de Diaken:
- `ansible_host` - IP del host
- `ansible_user` - Usuario SSH
- `ansible_ssh_private_key_file` - Llave SSH
- Variables personalizadas definidas en el deployment

