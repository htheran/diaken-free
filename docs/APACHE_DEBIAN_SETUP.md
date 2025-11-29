# Configuración de Apache para Debian/Ubuntu

## Resumen

Este documento describe la configuración de Apache2 para sistemas Debian/Ubuntu utilizando variables globales y plantillas Jinja2.

## Variables Globales

Todas las variables están en la sección **Apache Variables** en Settings:

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `debian_apache_user` | www-data | Usuario del servicio Apache |
| `debian_apache_group` | www-data | Grupo del servicio Apache |
| `debian_server_root` | /opt/www/sites | Directorio raíz para sitios web |
| `debian_log_root` | /var/log/apache2/sites | Directorio de logs |
| `debian_http_port` | 80 | Puerto HTTP |

## Plantillas J2

### 1. apache2.conf.j2
**Ubicación:** `media/j2/host/apache2.conf.j2`  
**Propósito:** Configuración principal de Apache2  
**Registrada en BD:** Sí (ID: 8)

**Variables utilizadas:**
- `{{ debian_http_port }}`
- `{{ debian_apache_user }}`
- `{{ debian_apache_group }}`
- `{{ debian_server_root }}`
- `{{ debian_log_root }}`
- `{{ inventory_hostname }}`

### 2. apache2-vhost.conf.j2
**Ubicación:** `media/j2/host/apache2-vhost.conf.j2`  
**Propósito:** Configuración de VirtualHost  
**Registrada en BD:** Sí (ID: 9)

**Variables utilizadas:**
- `{{ debian_http_port }}`
- `{{ inventory_hostname }}`
- `{{ debian_server_root }}`
- `{{ debian_log_root }}`

**Características:**
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Compresión (mod_deflate)
- Caché del navegador (mod_expires)
- Soporte PHP (si está instalado)

## Playbook

**Archivo:** `media/playbooks/host/Install-Apache-Debian-Host.yml`  
**Registrado en BD:** Sí (ID: 14)

### Características

1. **Sin variables hardcodeadas:** Todas las variables vienen de Global Settings
2. **Usa plantillas J2:** Para configuración de VirtualHost
3. **Idempotente:** Se puede ejecutar múltiples veces sin problemas
4. **Tags organizados:** Para ejecución selectiva

### Tags disponibles

```bash
# Ejecutar solo instalación
ansible-playbook playbook.yml --tags installation

# Ejecutar solo configuración de VirtualHost
ansible-playbook playbook.yml --tags vhost

# Saltar firewall
ansible-playbook playbook.yml --skip-tags firewall

# Solo verificación
ansible-playbook playbook.yml --tags verification
```

### Estructura de tareas

1. **Preparación** (tags: preparation, ansible_tmp, hostname)
   - Crear directorio temporal de Ansible
   - Configurar hostname
   - Actualizar cache de paquetes

2. **Instalación** (tags: httpd, installation, service)
   - Instalar Apache2 y utilidades
   - Iniciar y habilitar servicio

3. **Firewall** (tags: firewall)
   - Configurar UFW (si está instalado)
   - Permitir puertos 80 y 443

4. **Directorios** (tags: httpd, directories)
   - Crear estructura de directorios
   - Configurar permisos

5. **Contenido** (tags: httpd, content)
   - Crear página de inicio por defecto

6. **VirtualHost** (tags: httpd, vhost, modules)
   - Aplicar plantilla J2
   - Habilitar módulos necesarios
   - Habilitar sitio

7. **Verificación** (tags: httpd, verification, service)
   - Verificar sintaxis de Apache
   - Reiniciar servicio
   - Verificar puerto abierto

## Instalación en Otro Servidor

### Opción 1: Usando Git

```bash
# 1. Clonar repositorio
cd /opt/www/app/diaken-pdn
git pull origin main

# 2. Aplicar variables en BD
mysql -u root -p diaken_db < sc/add_apache_variables.sql

# 3. Verificar plantillas
ls -l media/j2/host/apache2*.j2

# 4. Reiniciar Apache (si es necesario)
sudo systemctl restart httpd
```

### Opción 2: Manual

1. **Crear sección en Settings:**
   - Nombre: "Apache Variables"
   - Descripción: "Configuración de Apache para sistemas Debian/Ubuntu"

2. **Agregar variables:**
   - Ir a Settings → Global Settings
   - Crear cada variable de la tabla anterior

3. **Subir plantillas:**
   - Ir a Settings → Ansible Templates
   - Subir `apache2.conf.j2`
   - Subir `apache2-vhost.conf.j2`

4. **Verificar playbook:**
   - El playbook debe estar en `media/playbooks/host/Install-Apache-Debian-Host.yml`
   - Verificar que esté registrado en BD

## Comparación con RedHat

| Aspecto | RedHat | Debian |
|---------|--------|--------|
| **Servicio** | httpd | apache2 |
| **Usuario** | apache | www-data |
| **Grupo** | apache | www-data |
| **Config dir** | /etc/httpd | /etc/apache2 |
| **Sites dir** | conf.d | sites-available/sites-enabled |
| **Comando test** | httpd -t | apache2ctl configtest |
| **Habilitar sitio** | N/A | a2ensite |
| **Habilitar módulo** | N/A | a2enmod |

## Resultado Final

Después de ejecutar el playbook:

1. ✅ Apache2 instalado y corriendo
2. ✅ VirtualHost configurado para el hostname
3. ✅ Directorio web: `/opt/www/sites/{hostname}/`
4. ✅ Logs: `/var/log/apache2/sites/{hostname}/`
5. ✅ Página de inicio moderna accesible
6. ✅ Firewall configurado (puertos 80 y 443)
7. ✅ Módulos necesarios habilitados:
   - rewrite
   - headers
   - expires
   - deflate
8. ✅ Sitio por defecto deshabilitado

## Troubleshooting

### Error: Variables no encontradas

```bash
# Verificar que las variables existan
python manage.py shell --settings=diaken.settings_production -c "
from settings.models import GlobalSetting
vars = GlobalSetting.objects.filter(key__startswith='debian_')
for v in vars:
    print(f'{v.key} = {v.value}')
"
```

### Error: Plantilla no encontrada

```bash
# Verificar que las plantillas existan
ls -l media/j2/host/apache2*.j2

# Verificar en BD
python manage.py shell --settings=diaken.settings_production -c "
from settings.models import AnsibleTemplate
templates = AnsibleTemplate.objects.filter(name__icontains='apache2')
for t in templates:
    print(f'{t.name}: {t.file.name}')
"
```

### Error: Módulo no encontrado

```bash
# Verificar módulos disponibles
apache2ctl -M

# Habilitar módulo manualmente
sudo a2enmod rewrite
sudo systemctl restart apache2
```

## Mantenimiento

### Actualizar variables

1. Ir a Settings → Global Settings
2. Buscar "Apache Variables"
3. Editar valores según necesidad
4. Re-ejecutar playbook

### Actualizar plantillas

1. Editar archivo en `media/j2/host/`
2. O subir nueva versión en Settings → Ansible Templates
3. Re-ejecutar playbook

## Seguridad

Las plantillas incluyen:

- ✅ Security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- ✅ ServerTokens Prod (oculta versión)
- ✅ ServerSignature Off
- ✅ TraceEnable Off
- ✅ Restricción de acceso a archivos sensibles (.htaccess, .bak, .sql, etc.)
- ✅ Referrer-Policy

## Logs

- **Error log:** `/var/log/apache2/sites/{hostname}/error.log`
- **Access log:** `/var/log/apache2/sites/{hostname}/access.log`

## Soporte

Para más información, consultar:
- Documentación de Apache2: https://httpd.apache.org/docs/
- Documentación de Ansible: https://docs.ansible.com/
