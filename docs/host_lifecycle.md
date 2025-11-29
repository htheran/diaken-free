# Ciclo de Vida de Hosts en Diaken

## Descripción

Este documento describe el ciclo de vida completo de un host en Diaken, desde su creación hasta su eliminación, incluyendo la gestión automática de `/etc/hosts`.

---

## 1. Creación de Host

### Métodos de Creación

#### A. Deployment Automático (Nueva VM)
```python
# En deploy/views.py después de deployment exitoso
new_host = Host.objects.create(
    name=hostname,
    ip=ip_address,
    environment=environment,
    group=group,
    operating_system='redhat',
    deployment_credential=ssh_credential,
    active=True,
    vcenter_server=vcenter_host,
)
# ✅ Host.save() se ejecuta automáticamente
# ✅ update_etc_hosts() se llama automáticamente
# ✅ /etc/hosts se actualiza con el nuevo host
```

**Resultado**:
- ✅ Host agregado al inventario
- ✅ Host agregado a `/etc/hosts`
- ✅ Hostname resuelve a IP correcta

#### B. Creación Manual (Admin Django)
```
1. Usuario accede a Django Admin
2. Navega a Inventory → Hosts → Add Host
3. Completa formulario (name, ip, environment, etc.)
4. Click en "Save"
```

**Resultado**:
- ✅ `Host.save()` se ejecuta
- ✅ `update_etc_hosts()` se llama automáticamente
- ✅ `/etc/hosts` se actualiza

#### C. Importación Masiva
```python
# Script de importación
hosts_data = [
    {'name': 'server01', 'ip': '10.100.1.10'},
    {'name': 'server02', 'ip': '10.100.1.11'},
    # ...
]

for data in hosts_data:
    Host.objects.create(**data)
    # update_etc_hosts() se llama para cada uno
```

---

## 2. Modificación de Host

### Cambios que Actualizan /etc/hosts

#### A. Cambio de IP
```python
host = Host.objects.get(name='prueba009')
host.ip = '10.100.5.90'  # Nueva IP
host.save()
# ✅ update_etc_hosts() se llama automáticamente
# ✅ /etc/hosts se actualiza con la nueva IP
```

**Antes**:
```
10.100.5.89     prueba009
```

**Después**:
```
10.100.5.90     prueba009
```

#### B. Cambio de Hostname
```python
host = Host.objects.get(name='prueba009')
host.name = 'prueba009-new'
host.save()
# ✅ update_etc_hosts() se llama automáticamente
```

#### C. Activar/Desactivar Host
```python
# Desactivar host
host = Host.objects.get(name='prueba009')
host.active = False
host.save()
# ✅ Host se ELIMINA de /etc/hosts (solo hosts activos)

# Reactivar host
host.active = True
host.save()
# ✅ Host se AGREGA nuevamente a /etc/hosts
```

---

## 3. Eliminación de Host

### Proceso Automático

```python
# Eliminar host del inventario
host = Host.objects.get(name='prueba009')
host.delete()
# ✅ remove_from_etc_hosts() se llama ANTES de eliminar
# ✅ Host se elimina de /etc/hosts
# ✅ Luego se elimina del inventario
```

### Implementación en Código

```python
# inventory/models.py
def delete(self, *args, **kwargs):
    # Remove from /etc/hosts before deleting
    self.remove_from_etc_hosts()
    super().delete(*args, **kwargs)
```

### Qué Hace `remove_from_etc_hosts()`

1. Lee `/etc/hosts` completo
2. Encuentra la sección entre marcadores
3. Obtiene todos los hosts activos **EXCEPTO el que se está eliminando**
4. Regenera la sección con los hosts restantes
5. Escribe el archivo actualizado

**Código**:
```python
# Get all active hosts EXCEPT this one
all_hosts = Host.objects.filter(active=True).exclude(id=self.id).order_by('name')

# Build managed section
managed_lines = [marker_start + '\n']
for host in all_hosts:
    managed_lines.append(f"{host.ip}\t{host.name}\n")
managed_lines.append(marker_end + '\n')
```

---

## 4. Reciclaje de IP o Hostname

### Escenario 1: Reutilizar IP

```python
# Eliminar host antiguo
old_host = Host.objects.get(name='prueba009')
old_host.delete()
# ✅ 10.100.5.89 se elimina de /etc/hosts

# Crear nuevo host con la misma IP
new_host = Host.objects.create(
    name='prueba010',
    ip='10.100.5.89',  # Misma IP
    environment=env,
    active=True
)
# ✅ 10.100.5.89 se agrega a /etc/hosts con nuevo hostname
```

**Resultado en /etc/hosts**:
```
# Antes:
10.100.5.89     prueba009

# Después de eliminar:
# (línea eliminada)

# Después de crear nuevo:
10.100.5.89     prueba010
```

### Escenario 2: Reutilizar Hostname

```python
# Eliminar host antiguo
old_host = Host.objects.get(name='prueba009')
old_host.delete()
# ✅ prueba009 se elimina de /etc/hosts

# Crear nuevo host con el mismo hostname pero diferente IP
new_host = Host.objects.create(
    name='prueba009',  # Mismo hostname
    ip='10.100.6.100',  # Nueva IP
    environment=env,
    active=True
)
# ✅ prueba009 se agrega a /etc/hosts con nueva IP
```

**Resultado en /etc/hosts**:
```
# Antes:
10.100.5.89     prueba009

# Después de eliminar:
# (línea eliminada)

# Después de crear nuevo:
10.100.6.100    prueba009
```

---

## 5. Verificación del Ciclo de Vida

### Comando de Verificación

```bash
# Ver hosts en inventario vs /etc/hosts
python manage.py shell -c "
from inventory.models import Host
import subprocess

print('=== HOSTS EN INVENTARIO (activos) ===')
hosts = Host.objects.filter(active=True).order_by('name')
for h in hosts:
    print(f'{h.ip}\t{h.name}')

print('\n=== HOSTS EN /etc/hosts ===')
result = subprocess.run(['grep', '-A', '100', 'Diaken Managed Hosts', '/etc/hosts'], 
                       capture_output=True, text=True)
print(result.stdout)
"
```

### Prueba de Eliminación

```bash
# 1. Ver hosts actuales
python manage.py shell -c "from inventory.models import Host; print(f'Total: {Host.objects.filter(active=True).count()}')"

# 2. Eliminar un host de prueba
python manage.py shell -c "
from inventory.models import Host
host = Host.objects.filter(name='test-host').first()
if host:
    print(f'Eliminando: {host.name} ({host.ip})')
    host.delete()
    print('✅ Host eliminado')
else:
    print('Host no encontrado')
"

# 3. Verificar que se eliminó de /etc/hosts
grep test-host /etc/hosts
# Debe retornar: exit code 1 (no encontrado)

# 4. Verificar conteo
python manage.py shell -c "from inventory.models import Host; print(f'Total después: {Host.objects.filter(active=True).count()}')"
```

---

## 6. Casos Especiales

### A. Eliminación Masiva

```python
# Eliminar múltiples hosts
hosts_to_delete = Host.objects.filter(
    environment__name='Testing',
    active=True
)

for host in hosts_to_delete:
    host.delete()
    # ✅ remove_from_etc_hosts() se llama para cada uno
    # ✅ /etc/hosts se actualiza cada vez
```

**Nota**: Cada eliminación actualiza `/etc/hosts` individualmente. Para eliminaciones masivas, considerar:

```python
# Opción más eficiente
hosts_to_delete = Host.objects.filter(environment__name='Testing')
hosts_to_delete.delete()  # Eliminación en bulk
# Luego forzar actualización única
remaining_host = Host.objects.filter(active=True).first()
if remaining_host:
    remaining_host.update_etc_hosts()
```

### B. Desactivar vs Eliminar

**Desactivar** (recomendado para histórico):
```python
host.active = False
host.save()
# ✅ Se elimina de /etc/hosts
# ✅ Permanece en inventario para histórico
# ✅ Puede reactivarse después
```

**Eliminar** (permanente):
```python
host.delete()
# ✅ Se elimina de /etc/hosts
# ✅ Se elimina del inventario
# ❌ No se puede recuperar
```

### C. Migración de Ambiente

```python
# Mover host a otro ambiente
host = Host.objects.get(name='prueba009')
host.environment = Environment.objects.get(name='Production')
host.save()
# ✅ update_etc_hosts() se llama
# ✅ /etc/hosts se mantiene actualizado
# (La IP y hostname no cambian, solo el ambiente)
```

---

## 7. Logs y Auditoría

### Ver Logs de Cambios

```bash
# Logs de actualización de /etc/hosts
sudo journalctl -xeu httpd.service | grep "Updated /etc/hosts"

# Logs de eliminación
sudo journalctl -xeu httpd.service | grep "Removed.*from /etc/hosts"
```

### Ejemplos de Logs

```
INFO: Updated /etc/hosts: Added/updated prueba009 (10.100.5.89). Total managed hosts: 5
INFO: Removed prueba009 (10.100.5.89) from /etc/hosts
```

---

## 8. Mejores Prácticas

### ✅ Recomendaciones

1. **Desactivar antes de eliminar**
   - Permite mantener histórico
   - Facilita auditoría
   - Puede reactivarse si fue error

2. **Verificar antes de reutilizar IP/hostname**
   ```bash
   # Verificar que no existe
   python manage.py shell -c "from inventory.models import Host; print(Host.objects.filter(name='prueba009').exists())"
   ```

3. **Backup antes de eliminaciones masivas**
   ```bash
   sudo cp /etc/hosts /etc/hosts.backup.$(date +%Y%m%d_%H%M%S)
   ```

4. **Usar comando de verificación**
   ```bash
   python manage.py update_hosts_file --dry-run
   ```

### ❌ Evitar

1. **No editar /etc/hosts manualmente** entre los marcadores
2. **No eliminar los marcadores** de Diaken
3. **No crear hosts duplicados** (mismo nombre o IP)

---

## 9. Troubleshooting

### Problema: Host eliminado pero sigue en /etc/hosts

**Causa**: Error en el proceso de eliminación

**Solución**:
```bash
# Forzar actualización completa
python manage.py update_hosts_file
```

### Problema: /etc/hosts tiene hosts que no están en inventario

**Causa**: Edición manual o corrupción

**Solución**:
```bash
# Regenerar completamente desde inventario
python manage.py update_hosts_file
```

### Problema: No se puede reutilizar IP

**Causa**: Host anterior no se eliminó correctamente

**Solución**:
```bash
# 1. Verificar hosts con esa IP
python manage.py shell -c "from inventory.models import Host; print(Host.objects.filter(ip='10.100.5.89'))"

# 2. Eliminar host antiguo
python manage.py shell -c "from inventory.models import Host; Host.objects.filter(ip='10.100.5.89').delete()"

# 3. Verificar /etc/hosts
grep 10.100.5.89 /etc/hosts
```

---

## 10. Resumen del Flujo

```
CREACIÓN:
Host.objects.create() → save() → update_etc_hosts() → /etc/hosts actualizado

MODIFICACIÓN:
host.save() → update_etc_hosts() → /etc/hosts actualizado

DESACTIVACIÓN:
host.active = False → save() → update_etc_hosts() → eliminado de /etc/hosts

ELIMINACIÓN:
host.delete() → remove_from_etc_hosts() → eliminado de /etc/hosts → eliminado de DB

RECICLAJE:
delete() → create() → /etc/hosts actualizado con nueva info
```

---

## Referencias

- Modelo Host: `inventory/models.py` (líneas 62-188)
- Comando manual: `inventory/management/commands/update_hosts_file.py`
- Documentación: `docs/hosts_file_management.md`

---

**Fecha**: 17 de Octubre 2025  
**Versión**: Diaken 1.0  
**Estado**: ✅ FUNCIONANDO - Ciclo de vida completo implementado
