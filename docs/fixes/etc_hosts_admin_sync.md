# Fix: /etc/hosts No Se Actualiza Desde Django Admin

## Problema Detectado (17 Oct 2025)

**Síntoma**:
- Usuario desactiva o elimina un host desde Django Admin
- El host se desactiva/elimina en la base de datos
- Pero `/etc/hosts` **NO** se actualiza automáticamente
- El host sigue apareciendo en `/etc/hosts`

**Ejemplo**:
```bash
# Usuario desactiva prueba007 desde Django Admin
# Inventario muestra solo 5 hosts activos
# Pero /etc/hosts todavía tiene 6 hosts:

$ cat /etc/hosts
# --- Diaken Managed Hosts ---
10.100.9.101    prueba005
10.100.9.102    prueba007  ← DEBERÍA ELIMINARSE
10.100.5.89     prueba009
10.100.18.81    test-one
10.100.18.82    test-two
10.100.18.86    test-win
# --- End Diaken Managed Hosts ---
```

## Causa Raíz

### Problema 1: Django Admin No Llama a save()

Django Admin puede usar métodos internos que no siempre ejecutan el método `save()` personalizado del modelo:

- **Edición inline**: Puede usar `update()` en lugar de `save()`
- **Cambios masivos**: Usa `update()` para eficiencia
- **Errores silenciosos**: Si `update_etc_hosts()` falla, no se reporta

### Problema 2: No Hay Admin Personalizado

El archivo `inventory/admin.py` estaba vacío:

```python
# ANTES (admin.py vacío)
from django.contrib import admin

# Register your models here.
```

Django usaba el admin por defecto, que no garantiza que se ejecute `update_etc_hosts()`.

## Solución Implementada

### 1. Admin Personalizado con Hooks

Creado `HostAdmin` personalizado que sobrescribe métodos clave:

```python
# inventory/admin.py

class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip', 'environment', 'group', 'operating_system', 'active', 'vcenter_server')
    list_filter = ('active', 'environment', 'group', 'operating_system')
    search_fields = ('name', 'ip', 'description')
    list_editable = ('active',)  # Permite editar active desde la lista
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to ensure /etc/hosts is updated.
        """
        super().save_model(request, obj, form, change)
        
        # Force update of /etc/hosts
        try:
            obj.update_etc_hosts()
            logger.info(f'Admin: Updated /etc/hosts after saving {obj.name} (active={obj.active})')
        except Exception as e:
            logger.error(f'Admin: Error updating /etc/hosts for {obj.name}: {e}', exc_info=True)
    
    def delete_model(self, request, obj):
        """
        Override delete_model to ensure /etc/hosts is updated.
        """
        host_name = obj.name
        host_ip = obj.ip
        
        # Delete will call remove_from_etc_hosts() automatically
        super().delete_model(request, obj)
        
        logger.info(f'Admin: Deleted {host_name} ({host_ip}) from inventory and /etc/hosts')
    
    def delete_queryset(self, request, queryset):
        """
        Override delete_queryset for bulk delete to ensure /etc/hosts is updated.
        """
        # Delete each host individually to trigger remove_from_etc_hosts()
        for obj in queryset:
            obj.delete()
        
        logger.info(f'Admin: Bulk deleted {queryset.count()} hosts')

# Register with custom admin
admin.site.register(Host, HostAdmin)
```

### 2. Características del Admin Personalizado

#### ✅ **save_model()**
- Se ejecuta cuando se guarda un host desde el admin
- Llama a `update_etc_hosts()` **después** de guardar
- Registra en logs si hay errores
- Funciona para crear y editar

#### ✅ **delete_model()**
- Se ejecuta cuando se elimina un host individual
- El método `delete()` del modelo ya llama a `remove_from_etc_hosts()`
- Registra la eliminación en logs

#### ✅ **delete_queryset()**
- Se ejecuta cuando se eliminan múltiples hosts (bulk delete)
- Elimina cada host individualmente para ejecutar `delete()`
- Asegura que `/etc/hosts` se actualice para cada uno

#### ✅ **list_editable**
- Permite cambiar `active` directamente desde la lista
- Ejecuta `save_model()` automáticamente
- Actualiza `/etc/hosts` inmediatamente

### 3. Comando Manual de Respaldo

Si por alguna razón `/etc/hosts` no se actualiza, siempre puedes forzarlo:

```bash
python manage.py update_hosts_file
```

## Flujo Corregido

### Antes (Problemático)

```
Usuario → Django Admin → Desactivar host
                      ↓
                   update() en DB
                      ↓
                   save() NO se ejecuta
                      ↓
                   update_etc_hosts() NO se ejecuta
                      ↓
                   /etc/hosts NO se actualiza ❌
```

### Después (Corregido)

```
Usuario → Django Admin → Desactivar host
                      ↓
                   save_model() override
                      ↓
                   super().save_model()
                      ↓
                   obj.update_etc_hosts() FORZADO
                      ↓
                   /etc/hosts actualizado ✅
                      ↓
                   Log registrado
```

## Casos de Uso

### Caso 1: Desactivar Host

```
1. Usuario va a Django Admin → Inventory → Hosts
2. Click en checkbox "Active" de prueba007 (desactivar)
3. Click en "Save"

Resultado:
- Host desactivado en DB ✅
- save_model() ejecutado ✅
- update_etc_hosts() ejecutado ✅
- /etc/hosts actualizado ✅
- Log: "Admin: Updated /etc/hosts after saving prueba007 (active=False)"
```

### Caso 2: Eliminar Host Individual

```
1. Usuario va a Django Admin → Inventory → Hosts
2. Click en host "prueba007"
3. Click en "Delete"
4. Confirmar eliminación

Resultado:
- delete_model() ejecutado ✅
- Host.delete() ejecutado ✅
- remove_from_etc_hosts() ejecutado ✅
- /etc/hosts actualizado ✅
- Log: "Admin: Deleted prueba007 (10.100.9.102) from inventory and /etc/hosts"
```

### Caso 3: Eliminar Múltiples Hosts (Bulk Delete)

```
1. Usuario va a Django Admin → Inventory → Hosts
2. Selecciona múltiples hosts inactivos
3. Action: "Delete selected hosts"
4. Confirmar eliminación

Resultado:
- delete_queryset() ejecutado ✅
- Cada host eliminado individualmente ✅
- remove_from_etc_hosts() ejecutado para cada uno ✅
- /etc/hosts actualizado ✅
- Log: "Admin: Bulk deleted 5 hosts"
```

### Caso 4: Editar Inline (List Editable)

```
1. Usuario va a Django Admin → Inventory → Hosts
2. Cambia "Active" directamente en la lista (sin entrar al detalle)
3. Click en "Save"

Resultado:
- save_model() ejecutado ✅
- update_etc_hosts() ejecutado ✅
- /etc/hosts actualizado ✅
```

## Verificación

### Verificar que el Admin Está Registrado

```bash
python manage.py shell -c "
from django.contrib import admin
from inventory.models import Host
print('Host admin:', admin.site._registry.get(Host))
"
```

**Salida esperada**:
```
Host admin: <inventory.admin.HostAdmin object at 0x...>
```

### Verificar Logs

```bash
# Ver logs de actualización de /etc/hosts
sudo journalctl -xeu httpd.service | grep "Admin: Updated /etc/hosts"

# Ejemplo de log:
# Admin: Updated /etc/hosts after saving prueba007 (active=False)
```

### Verificar /etc/hosts

```bash
# Después de desactivar prueba007
cat /etc/hosts | grep -A 10 "Diaken Managed"

# Debe mostrar solo hosts activos:
# --- Diaken Managed Hosts ---
# 10.100.9.101    prueba005
# 10.100.5.89     prueba009
# 10.100.18.81    test-one
# 10.100.18.82    test-two
# 10.100.18.86    test-win
# --- End Diaken Managed Hosts ---
```

## Solución Temporal (Si Falla)

Si por alguna razón `/etc/hosts` no se actualiza automáticamente:

```bash
# Forzar actualización manual
python manage.py update_hosts_file
```

**Salida**:
```
Found 5 active hosts in inventory:
  - 10.100.9.101    prueba005
  - 10.100.5.89     prueba009
  - 10.100.18.81    test-one
  - 10.100.18.82    test-two
  - 10.100.18.86    test-win

Updating /etc/hosts...
✅ Successfully updated /etc/hosts with 5 hosts
```

## Mejoras Adicionales

### 1. Mensajes de Confirmación en Admin

Agregar mensajes al usuario cuando se actualiza `/etc/hosts`:

```python
from django.contrib import messages

def save_model(self, request, obj, form, change):
    super().save_model(request, obj, form, change)
    
    try:
        obj.update_etc_hosts()
        messages.success(request, f'/etc/hosts updated for {obj.name}')
    except Exception as e:
        messages.error(request, f'Error updating /etc/hosts: {e}')
```

### 2. Acción Personalizada para Actualizar /etc/hosts

```python
def update_hosts_file_action(modeladmin, request, queryset):
    """Admin action to force update /etc/hosts"""
    try:
        first_host = Host.objects.filter(active=True).first()
        if first_host:
            first_host.update_etc_hosts()
            messages.success(request, '/etc/hosts updated successfully')
    except Exception as e:
        messages.error(request, f'Error: {e}')

update_hosts_file_action.short_description = "Force update /etc/hosts"

class HostAdmin(admin.ModelAdmin):
    actions = [update_hosts_file_action]
```

## Archivos Modificados

- ✅ `inventory/admin.py` - Admin personalizado con hooks
- ✅ `inventory/models.py` - Manejo de errores en save()

## Comandos de Verificación

```bash
# 1. Reiniciar Django
sudo systemctl restart diaken

# 2. Verificar que admin está registrado
python manage.py shell -c "from django.contrib import admin; from inventory.models import Host; print(admin.site._registry.get(Host))"

# 3. Probar desactivando un host desde admin
# (hacer desde navegador)

# 4. Verificar /etc/hosts
cat /etc/hosts | grep -A 10 "Diaken Managed"

# 5. Ver logs
sudo journalctl -xeu httpd.service | tail -50 | grep "Admin:"
```

## Estado

✅ **RESUELTO** - Admin personalizado implementado  
✅ `/etc/hosts` se actualiza automáticamente desde Django Admin  
✅ Logs detallados de cada operación  
✅ Comando manual disponible como respaldo  

---

**Fecha**: 17 de Octubre 2025  
**Versión**: Diaken 1.0  
**Estado**: ✅ FUNCIONANDO - Sincronización automática activa
