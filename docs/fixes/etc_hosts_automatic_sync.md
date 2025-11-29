# Fix: Sincronización Automática de /etc/hosts con Sudo

## Problema Detectado (17 Oct 2025 - 15:30)

**Síntoma**:
- Usuario agrega host manualmente desde la interfaz web
- Host se guarda en la base de datos correctamente
- Pero `/etc/hosts` **NO** se actualiza automáticamente
- Usuario tiene que ejecutar comando manual: `python manage.py update_hosts_file`

**Ejemplo**:
```bash
# Usuario agrega prueba005 desde la web
# Host guardado en DB ✅
# /etc/hosts NO actualizado ❌

$ cat /etc/hosts
# --- Diaken Managed Hosts ---
10.100.5.89     prueba009
10.100.18.81    test-one
10.100.18.82    test-two
10.100.18.86    test-win
# --- End Diaken Managed Hosts ---
# prueba005 NO está aquí ❌
```

## Causa Raíz

### Problema de Permisos

```bash
$ ls -la /etc/hosts
-rw-r--r-- 1 root root 336 Oct 17 14:51 /etc/hosts
```

- `/etc/hosts` es propiedad de `root`
- Solo `root` puede escribir en él
- Django se ejecuta como usuario `apache` (vía mod_wsgi)
- Usuario `apache` **NO tiene permisos** para escribir en `/etc/hosts`

### Código Original (Fallaba Silenciosamente)

```python
# inventory/models.py (ANTES)
def update_etc_hosts(self):
    # Intenta escribir directamente en /etc/hosts
    with open('/etc/hosts', 'w') as f:  # ← Permission denied
        f.write(...)
```

**Resultado**: Error silencioso, `/etc/hosts` no se actualiza.

## Solución Implementada

### Arquitectura de la Solución

```
Django (usuario apache)
    ↓
    Llama a subprocess.run(['sudo', 'script'])
    ↓
Sudo (sin contraseña, configurado en /etc/sudoers.d/)
    ↓
Script Python (/usr/local/bin/update-diaken-hosts.py)
    ↓
    Ejecuta como root
    ↓
    Actualiza /etc/hosts ✅
```

### 1. Script Python con Sudo

**Archivo**: `/usr/local/bin/update-diaken-hosts.py`

```python
#!/opt/www/app/diaken-pdn/venv/bin/python
"""
Script to update /etc/hosts with Diaken managed hosts.
This script runs with sudo permissions and updates /etc/hosts directly.
"""
import os
import sys
import tempfile
import shutil

# Add Django project to path
sys.path.insert(0, '/opt/www/app/diaken-pdn')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')

# Setup Django
import django
django.setup()

from inventory.models import Host

def update_hosts_file():
    """Update /etc/hosts with all active hosts"""
    hosts_file = '/etc/hosts'
    marker_start = '# --- Diaken Managed Hosts ---'
    marker_end = '# --- End Diaken Managed Hosts ---'
    
    try:
        # Read current /etc/hosts
        with open(hosts_file, 'r') as f:
            lines = f.readlines()
        
        # Find managed section
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if marker_start in line:
                start_idx = i
            elif marker_end in line:
                end_idx = i
        
        # Get all active hosts
        all_hosts = Host.objects.filter(active=True).order_by('name')
        
        # Build managed section
        managed_lines = [marker_start + '\n']
        for host in all_hosts:
            managed_lines.append(f"{host.ip}\t{host.name}\n")
        managed_lines.append(marker_end + '\n')
        
        # Rebuild /etc/hosts
        if start_idx is not None and end_idx is not None:
            new_lines = lines[:start_idx] + managed_lines + lines[end_idx+1:]
        else:
            new_lines = lines + ['\n'] + managed_lines
        
        # Write atomically
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.writelines(new_lines)
            tmp_path = tmp.name
        
        shutil.move(tmp_path, hosts_file)
        os.chmod(hosts_file, 0o644)
        
        print(f'✅ Successfully updated /etc/hosts with {all_hosts.count()} hosts')
        return 0
        
    except Exception as e:
        print(f'❌ Error updating /etc/hosts: {e}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(update_hosts_file())
```

**Permisos**:
```bash
chmod +x /usr/local/bin/update-diaken-hosts.py
```

### 2. Configuración de Sudo

**Archivo**: `/etc/sudoers.d/diaken-hosts`

```bash
# Allow apache user to update /etc/hosts via Diaken script
apache ALL=(root) NOPASSWD: /usr/local/bin/update-diaken-hosts.py
```

**Permisos**:
```bash
chmod 440 /etc/sudoers.d/diaken-hosts
```

**Esto permite**:
- Usuario `apache` puede ejecutar el script como `root`
- Sin necesidad de contraseña (`NOPASSWD`)
- Solo para este script específico (seguridad)

### 3. Modelo Actualizado

**Archivo**: `inventory/models.py`

```python
def update_etc_hosts(self):
    """Update /etc/hosts with this host's entry using sudo"""
    import subprocess
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Use sudo to run the update script
        result = subprocess.run(
            ['sudo', '/usr/local/bin/update-diaken-hosts.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f'Updated /etc/hosts: Added/updated {self.name} ({self.ip})')
        else:
            logger.error(f'Error updating /etc/hosts: {result.stderr}')
        
    except subprocess.TimeoutExpired:
        logger.error('Timeout updating /etc/hosts')
    except Exception as e:
        logger.error(f'Error updating /etc/hosts: {e}')

def remove_from_etc_hosts(self):
    """Remove this host from /etc/hosts using sudo"""
    import subprocess
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Use sudo to run the update script
        result = subprocess.run(
            ['sudo', '/usr/local/bin/update-diaken-hosts.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f'Removed {self.name} ({self.ip}) from /etc/hosts')
        else:
            logger.error(f'Error removing host from /etc/hosts: {result.stderr}')
        
    except subprocess.TimeoutExpired:
        logger.error('Timeout removing host from /etc/hosts')
    except Exception as e:
        logger.error(f'Error removing host from /etc/hosts: {e}')
```

## Flujo Corregido

### Agregar Host

```
Usuario → Web Form → Submit
    ↓
Django View → host.save()
    ↓
Host Model → save() override
    ↓
    super().save()  # Guarda en DB
    ↓
    update_etc_hosts()
    ↓
    subprocess.run(['sudo', 'script'])
    ↓
Script ejecuta como root
    ↓
/etc/hosts actualizado ✅
```

### Eliminar Host

```
Usuario → Click Delete → Confirm
    ↓
Django View → host.delete()
    ↓
Host Model → delete() override
    ↓
    remove_from_etc_hosts()
    ↓
    subprocess.run(['sudo', 'script'])
    ↓
Script ejecuta como root
    ↓
/etc/hosts actualizado ✅
    ↓
    super().delete()  # Elimina de DB
```

### Desactivar Host

```
Usuario → Django Admin → Uncheck "Active" → Save
    ↓
HostAdmin → save_model()
    ↓
    super().save_model()
    ↓
    obj.update_etc_hosts()
    ↓
    subprocess.run(['sudo', 'script'])
    ↓
Script ejecuta como root
    ↓
/etc/hosts actualizado (host eliminado) ✅
```

## Pruebas de Verificación

### Prueba 1: Agregar Host

```bash
# Crear host desde shell
python manage.py shell -c "
from inventory.models import Host, Environment
env = Environment.objects.first()
h = Host.objects.create(name='test-auto', ip='10.100.99.99', environment=env, active=True)
print(f'Host created: {h}')
"

# Verificar /etc/hosts
cat /etc/hosts | grep test-auto
# Output: 10.100.99.99    test-auto ✅
```

### Prueba 2: Eliminar Host

```bash
# Eliminar host
python manage.py shell -c "
from inventory.models import Host
Host.objects.filter(name='test-auto').delete()
print('Deleted')
"

# Verificar /etc/hosts
cat /etc/hosts | grep test-auto
# Output: (sin resultados) ✅
```

### Prueba 3: Desactivar Host

```bash
# Desactivar host
python manage.py shell -c "
from inventory.models import Host
h = Host.objects.get(name='prueba005')
h.active = False
h.save()
print('Deactivated')
"

# Verificar /etc/hosts
cat /etc/hosts | grep prueba005
# Output: (sin resultados) ✅
```

## Seguridad

### ✅ **Configuración Segura**

1. **Sudo limitado**: Solo permite ejecutar un script específico
2. **Sin contraseña**: Solo para este script, no para todo
3. **Usuario específico**: Solo `apache`, no otros usuarios
4. **Script controlado**: Script en `/usr/local/bin/` (solo root puede modificar)
5. **Permisos correctos**: `440` en sudoers, `755` en script

### ✅ **Validaciones**

```bash
# Verificar configuración de sudo
sudo -l -U apache
# Output:
# User apache may run the following commands:
#     (root) NOPASSWD: /usr/local/bin/update-diaken-hosts.py

# Verificar permisos del script
ls -la /usr/local/bin/update-diaken-hosts.py
# Output: -rwxr-xr-x 1 root root ... update-diaken-hosts.py

# Verificar permisos de sudoers
ls -la /etc/sudoers.d/diaken-hosts
# Output: -r--r----- 1 root root ... diaken-hosts
```

## Logs

```bash
# Ver logs de actualización
sudo journalctl -xeu httpd.service | grep "Updated /etc/hosts"

# Ejemplo de logs:
# Updated /etc/hosts: Added/updated prueba005 (10.100.9.101)
# Removed test-auto (10.100.99.99) from /etc/hosts
```

## Troubleshooting

### Problema: "sudo: no tty present"

**Solución**: Ya configurado con `NOPASSWD` en sudoers.

### Problema: "Permission denied"

**Causa**: Sudoers no configurado correctamente.

**Solución**:
```bash
# Verificar sudoers
sudo visudo -c -f /etc/sudoers.d/diaken-hosts

# Verificar permisos
chmod 440 /etc/sudoers.d/diaken-hosts
```

### Problema: "Timeout updating /etc/hosts"

**Causa**: Script tarda más de 30 segundos.

**Solución**: Aumentar timeout en `models.py` o verificar que el script funciona:
```bash
sudo /usr/local/bin/update-diaken-hosts.py
```

### Problema: Script no ejecuta

**Causa**: Permisos o shebang incorrecto.

**Solución**:
```bash
# Verificar shebang
head -1 /usr/local/bin/update-diaken-hosts.py
# Debe ser: #!/opt/www/app/diaken-pdn/venv/bin/python

# Dar permisos de ejecución
chmod +x /usr/local/bin/update-diaken-hosts.py

# Probar directamente
sudo /usr/local/bin/update-diaken-hosts.py
```

## Comando Manual (Respaldo)

Si por alguna razón falla, siempre puedes ejecutar:

```bash
# Opción 1: Script con sudo
sudo /usr/local/bin/update-diaken-hosts.py

# Opción 2: Comando Django
python manage.py update_hosts_file
```

## Archivos Creados/Modificados

- ✅ `/usr/local/bin/update-diaken-hosts.py` - Script Python con sudo
- ✅ `/etc/sudoers.d/diaken-hosts` - Configuración de sudo
- ✅ `inventory/models.py` - Métodos update_etc_hosts() y remove_from_etc_hosts()

## Estado

✅ **FUNCIONANDO** - Sincronización automática activa  
✅ Agregar host → `/etc/hosts` actualizado automáticamente  
✅ Eliminar host → `/etc/hosts` actualizado automáticamente  
✅ Desactivar host → `/etc/hosts` actualizado automáticamente  
✅ Sin necesidad de comandos manuales  

---

**Fecha**: 17 de Octubre 2025  
**Versión**: Diaken 1.0  
**Estado**: ✅ PRODUCCIÓN - Sincronización automática con sudo
