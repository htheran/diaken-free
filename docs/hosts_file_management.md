# Gestión Automática de /etc/hosts - Diaken

## Descripción

Diaken gestiona automáticamente el archivo `/etc/hosts` del servidor para mantener sincronizados todos los hosts del inventario. Esto permite que Ansible pueda resolver los hostnames correctamente sin necesidad de DNS.

## Funcionamiento Automático

### Actualización Automática

El archivo `/etc/hosts` se actualiza automáticamente en los siguientes casos:

1. **Al agregar un host al inventario** (manual o por deployment)
2. **Al modificar un host** (cambio de IP o hostname)
3. **Al eliminar un host** del inventario
4. **Al activar/desactivar un host**

### Implementación

El modelo `Host` en `inventory/models.py` tiene métodos `save()` y `delete()` que llaman automáticamente a:
- `update_etc_hosts()` - Actualiza /etc/hosts con todos los hosts activos
- `remove_from_etc_hosts()` - Elimina el host de /etc/hosts

## Formato del Archivo /etc/hosts

```bash
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

# --- Diaken Managed Hosts ---
10.100.9.101    prueba005
10.100.5.89     prueba009
10.100.18.81    test-one
10.100.18.82    test-two
10.100.18.86    test-win
# --- End Diaken Managed Hosts ---
```

### Marcadores

- **`# --- Diaken Managed Hosts ---`**: Inicio de la sección gestionada
- **`# --- End Diaken Managed Hosts ---`**: Fin de la sección gestionada

**IMPORTANTE**: No editar manualmente entre estos marcadores, ya que los cambios se sobrescribirán automáticamente.

## Uso con Ansible

### Inventario Generado

Cuando se ejecuta un playbook, Diaken genera un inventario temporal con el siguiente formato:

```ini
[target_group]
prueba009 ansible_host=10.100.5.89 ansible_user=user_diaken ansible_ssh_private_key_file=/path/to/key.pem
test-one ansible_host=10.100.18.81 ansible_user=user_diaken ansible_ssh_private_key_file=/path/to/key.pem
```

### Ventajas

1. **Conexión por IP**: Ansible siempre se conecta usando `ansible_host=IP`, lo cual es más seguro y confiable
2. **Resolución de hostname**: El hostname se puede resolver localmente en el servidor Diaken
3. **Sin dependencia de DNS**: No requiere configuración de DNS externo
4. **Logs más legibles**: Los logs muestran hostnames en lugar de IPs

## Comandos de Gestión

### Actualizar /etc/hosts Manualmente

```bash
# Actualizar con todos los hosts activos
python manage.py update_hosts_file

# Ver qué se actualizaría sin hacer cambios
python manage.py update_hosts_file --dry-run
```

### Verificar Resolución de Hostname

```bash
# Verificar que un hostname se resuelve correctamente
getent hosts prueba009

# Ping por hostname
ping -c 1 prueba009

# SSH por hostname (usando la IP configurada en /etc/hosts)
ssh user@prueba009
```

### Ver Hosts en Inventario

```bash
# Ver todos los hosts activos
python manage.py shell -c "from inventory.models import Host; [print(f'{h.ip}\t{h.name}') for h in Host.objects.filter(active=True)]"
```

## Troubleshooting

### Problema: Hostname no se resuelve

**Síntoma**:
```
ssh: Could not resolve hostname prueba009: Name or service not known
```

**Solución**:
```bash
# 1. Verificar que el host está en el inventario
python manage.py shell -c "from inventory.models import Host; print(Host.objects.filter(name='prueba009').first())"

# 2. Forzar actualización de /etc/hosts
python manage.py update_hosts_file

# 3. Verificar que está en /etc/hosts
grep prueba009 /etc/hosts

# 4. Verificar resolución
getent hosts prueba009
```

### Problema: /etc/hosts no se actualiza automáticamente

**Causa posible**: Permisos incorrectos

**Solución**:
```bash
# Verificar permisos
ls -l /etc/hosts
# Debe ser: -rw-r--r-- 1 root root

# Verificar que el usuario apache puede escribir (a través de Django)
sudo -u apache python manage.py update_hosts_file --dry-run
```

### Problema: Hosts duplicados en /etc/hosts

**Causa**: Marcadores incorrectos o corruptos

**Solución**:
```bash
# 1. Backup del archivo actual
sudo cp /etc/hosts /etc/hosts.backup

# 2. Editar manualmente y asegurar que los marcadores estén correctos
sudo nano /etc/hosts

# 3. Forzar actualización
python manage.py update_hosts_file
```

## Integración con Deployment

### Flujo de Deployment

Cuando se despliega una nueva VM:

1. **VM se crea en vCenter**
2. **Provisioning con Ansible** (hostname, IP, red)
3. **VM se agrega al inventario** automáticamente
4. **`Host.save()` se ejecuta**
5. **`update_etc_hosts()` se llama automáticamente**
6. **`/etc/hosts` se actualiza** con el nuevo host
7. **Playbooks adicionales** pueden usar el hostname

### Código en deploy/views.py

```python
# Después de deployment exitoso
new_host = Host.objects.create(
    name=hostname,
    ip=ip_address,
    environment=environment,
    group=group,
    active=True,
    # ... otros campos ...
)
# update_etc_hosts() se llama automáticamente en save()
```

## Seguridad

### Mejores Prácticas

1. **Siempre usar `ansible_host=IP`** en inventarios
   - Más seguro que confiar solo en resolución de hostname
   - Evita ataques de DNS spoofing

2. **Verificar IP antes de agregar al inventario**
   - Validar que la IP es correcta
   - Verificar conectividad SSH

3. **Mantener /etc/hosts limpio**
   - Solo hosts activos
   - Eliminar hosts obsoletos del inventario

4. **Backup regular**
   ```bash
   sudo cp /etc/hosts /etc/hosts.backup.$(date +%Y%m%d)
   ```

## Display en UI

### Select de Hosts

En los formularios de Django, los hosts se muestran con el formato:
```
hostname (IP)
```

Ejemplo:
```
prueba009 (10.100.5.89)
test-one (10.100.18.81)
```

Esto se logra con el método `__str__()` del modelo:
```python
def __str__(self):
    return f"{self.name} ({self.ip})"
```

## Logs

### Ver Logs de Actualización

```bash
# Logs de Django
sudo journalctl -xeu httpd.service | grep "Updated /etc/hosts"

# Ejemplo de log exitoso:
# Updated /etc/hosts: Added/updated prueba009 (10.100.5.89). Total managed hosts: 5
```

## Comandos Útiles

```bash
# Ver todos los hosts en /etc/hosts
grep -A 100 "Diaken Managed Hosts" /etc/hosts | grep -B 100 "End Diaken"

# Contar hosts gestionados
grep -c "^\s*[0-9]" /etc/hosts

# Ver hosts activos en inventario
python manage.py shell -c "from inventory.models import Host; print(f'Active hosts: {Host.objects.filter(active=True).count()}')"

# Comparar inventario vs /etc/hosts
python manage.py update_hosts_file --dry-run
```

## Referencias

- Modelo Host: `inventory/models.py`
- Comando de actualización: `inventory/management/commands/update_hosts_file.py`
- Generación de inventario: `deploy/views_group.py`

---

**Fecha**: 17 de Octubre 2025  
**Versión**: Diaken 1.0  
**Estado**: ✅ FUNCIONANDO - Actualización automática activa
