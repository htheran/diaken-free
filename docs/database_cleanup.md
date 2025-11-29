# Limpieza de Base de Datos - Hosts Inactivos

## Problema

Con el tiempo, la base de datos se satura con hosts inactivos y duplicados:
- **78 hosts totales** en la base de datos
- **6 hosts activos** (los que realmente se usan)
- **72 hosts inactivos** (saturando la DB)

### Ejemplos de Duplicados

- `prueba005`: 19 duplicados inactivos + 1 activo = 20 registros
- `prueba009`: 12 duplicados inactivos + 1 activo = 13 registros
- `prueba006`: 10 duplicados inactivos
- `prueba007`: 5 duplicados inactivos + 1 activo = 6 registros

## Solución: Comando de Limpieza

### Comando Creado

```bash
python manage.py cleanup_inactive_hosts
```

### Opciones Disponibles

#### 1. Ver qué se eliminaría (Dry Run)

```bash
# Ver todos los hosts inactivos que se eliminarían
python manage.py cleanup_inactive_hosts --all-inactive --dry-run

# Ver duplicados
python manage.py cleanup_inactive_hosts --duplicates --dry-run
```

**Salida**:
```
=== CLEANUP INACTIVE HOSTS ===

Total hosts in database: 78
Active hosts: 6
Inactive hosts: 72

=== ACTIVE HOSTS (will be kept) ===
  ✓ prueba005 (10.100.9.101)
  ✓ prueba007 (10.100.9.102)
  ✓ prueba009 (10.100.5.89)
  ✓ test-one (10.100.18.81)
  ✓ test-two (10.100.18.82)
  ✓ test-win (10.100.18.86)

=== ALL INACTIVE HOSTS (to be deleted) ===
  prueba005 (DUPLICATES: 19):
    - ID: 4, IP: 10.100.18.86, Active: False
    - ID: 5, IP: 10.100.18.86, Active: False
    ...

Total hosts to delete: 72
```

#### 2. Eliminar TODOS los hosts inactivos

```bash
# Ver primero (dry-run)
python manage.py cleanup_inactive_hosts --all-inactive --dry-run

# Eliminar (requiere confirmación)
python manage.py cleanup_inactive_hosts --all-inactive
```

**Confirmación requerida**:
```
⚠️  WARNING: This will permanently delete 72 hosts!
Are you sure you want to continue? (yes/no): yes
```

#### 3. Eliminar hosts inactivos por antigüedad

```bash
# Eliminar hosts inactivos de más de 30 días (default)
python manage.py cleanup_inactive_hosts

# Eliminar hosts inactivos de más de 7 días
python manage.py cleanup_inactive_hosts --days 7

# Eliminar hosts inactivos de más de 90 días
python manage.py cleanup_inactive_hosts --days 90
```

#### 4. Eliminar solo duplicados

```bash
# Ver duplicados (dry-run)
python manage.py cleanup_inactive_hosts --duplicates --dry-run

# Eliminar duplicados (mantiene el más reciente activo)
python manage.py cleanup_inactive_hosts --duplicates
```

## Proceso de Limpieza

### Paso 1: Revisar Hosts Activos

```bash
python manage.py shell -c "
from inventory.models import Host
hosts = Host.objects.filter(active=True).order_by('name')
print('=== ACTIVE HOSTS ===')
for h in hosts:
    print(f'{h.name}: {h.ip}')
"
```

**Resultado esperado**:
```
=== ACTIVE HOSTS ===
prueba005: 10.100.9.101
prueba007: 10.100.9.102
prueba009: 10.100.5.89
test-one: 10.100.18.81
test-two: 10.100.18.82
test-win: 10.100.18.86
```

### Paso 2: Dry Run (Simular)

```bash
python manage.py cleanup_inactive_hosts --all-inactive --dry-run
```

Esto muestra:
- ✅ Hosts activos que se mantendrán
- ❌ Hosts inactivos que se eliminarán
- 📊 Estadísticas de duplicados
- 🔢 Total a eliminar

### Paso 3: Ejecutar Limpieza

```bash
python manage.py cleanup_inactive_hosts --all-inactive
```

**Proceso**:
1. Muestra resumen
2. Pide confirmación: `yes`
3. Elimina hosts uno por uno
4. Actualiza `/etc/hosts` automáticamente
5. Muestra estadísticas finales

### Paso 4: Verificar Resultado

```bash
# Ver total de hosts
python manage.py shell -c "
from inventory.models import Host
print(f'Total: {Host.objects.count()}')
print(f'Active: {Host.objects.filter(active=True).count()}')
print(f'Inactive: {Host.objects.filter(active=False).count()}')
"
```

**Resultado esperado**:
```
Total: 6
Active: 6
Inactive: 0
```

## Ejemplo Completo de Limpieza

```bash
# 1. Ver estado actual
python manage.py shell -c "from inventory.models import Host; print(f'Total: {Host.objects.count()}')"
# Output: Total: 78

# 2. Ver qué se eliminaría
python manage.py cleanup_inactive_hosts --all-inactive --dry-run
# Output: Total hosts to delete: 72

# 3. Ejecutar limpieza
python manage.py cleanup_inactive_hosts --all-inactive
# Confirmar: yes

# 4. Verificar resultado
python manage.py shell -c "from inventory.models import Host; print(f'Total: {Host.objects.count()}')"
# Output: Total: 6

# 5. Verificar /etc/hosts
cat /etc/hosts | grep -A 10 "Diaken Managed"
```

## Qué Hace el Comando

### 1. Identifica Hosts a Eliminar

- Hosts con `active=False`
- Hosts duplicados (mismo nombre, diferentes IPs)
- Hosts antiguos (opcional, por días)

### 2. Protege Hosts Activos

- **NUNCA** elimina hosts con `active=True`
- Muestra lista de hosts activos que se mantendrán
- Requiere confirmación explícita

### 3. Elimina de Forma Segura

```python
# Para cada host inactivo:
host.delete()  # Esto ejecuta:
  1. remove_from_etc_hosts()  # Elimina de /etc/hosts
  2. super().delete()         # Elimina de DB
```

### 4. Actualiza /etc/hosts

Después de eliminar, actualiza `/etc/hosts` con solo los hosts activos:

```
# --- Diaken Managed Hosts ---
10.100.9.101    prueba005
10.100.9.102    prueba007
10.100.5.89     prueba009
10.100.18.81    test-one
10.100.18.82    test-two
10.100.18.86    test-win
# --- End Diaken Managed Hosts ---
```

## Beneficios

### Antes de la Limpieza

- 📊 **78 hosts** en la base de datos
- 🐌 Queries lentas
- 💾 Espacio desperdiciado
- 😵 Confusión con duplicados
- 📝 Logs saturados

### Después de la Limpieza

- 📊 **6 hosts** en la base de datos (92% reducción)
- ⚡ Queries rápidas
- 💾 Espacio optimizado
- 😊 Sin duplicados
- 📝 Logs limpios

## Recomendaciones

### Limpieza Regular

```bash
# Cada mes, eliminar hosts inactivos de más de 30 días
0 0 1 * * cd /opt/www/app/diaken-pdn && python manage.py cleanup_inactive_hosts --days 30
```

### Antes de Eliminar

1. ✅ Verificar que los hosts activos son correctos
2. ✅ Hacer backup de la base de datos
3. ✅ Ejecutar dry-run primero
4. ✅ Revisar la lista de hosts a eliminar

### Backup de Base de Datos

```bash
# Backup antes de limpieza
python manage.py dumpdata inventory.Host > /tmp/hosts_backup_$(date +%Y%m%d).json

# Restaurar si es necesario
python manage.py loaddata /tmp/hosts_backup_20251017.json
```

## Troubleshooting

### Problema: "No hosts to delete"

**Causa**: Todos los hosts están activos o no hay hosts inactivos.

**Solución**: Verificar hosts activos:
```bash
python manage.py shell -c "from inventory.models import Host; print(Host.objects.filter(active=False).count())"
```

### Problema: Error al eliminar host

**Causa**: Relaciones de clave foránea o permisos.

**Solución**: Ver logs:
```bash
sudo journalctl -xeu httpd.service | grep -i error
```

### Problema: /etc/hosts no se actualiza

**Causa**: Permisos o error en update_etc_hosts().

**Solución**: Forzar actualización:
```bash
python manage.py update_hosts_file
```

## Estadísticas de Ejemplo

### Caso Real (17 Oct 2025)

**Antes**:
```
Total hosts: 78
Active: 6 (7.7%)
Inactive: 72 (92.3%)

Duplicados:
- prueba005: 20 registros (19 inactivos)
- prueba009: 13 registros (12 inactivos)
- prueba006: 10 registros (10 inactivos)
- prueba007: 6 registros (5 inactivos)
```

**Después**:
```
Total hosts: 6
Active: 6 (100%)
Inactive: 0 (0%)

Sin duplicados
```

**Ahorro**:
- 92% reducción en registros
- 100% eliminación de duplicados
- Mejora en performance de queries
- Base de datos limpia y mantenible

## Comandos Útiles

```bash
# Ver total de hosts
python manage.py shell -c "from inventory.models import Host; print(f'Total: {Host.objects.count()}, Active: {Host.objects.filter(active=True).count()}, Inactive: {Host.objects.filter(active=False).count()}')"

# Ver duplicados por nombre
python manage.py shell -c "
from inventory.models import Host
from collections import Counter
names = [h.name for h in Host.objects.all()]
duplicates = {name: count for name, count in Counter(names).items() if count > 1}
print('Duplicates:', duplicates)
"

# Listar todos los hosts inactivos
python manage.py shell -c "
from inventory.models import Host
inactive = Host.objects.filter(active=False).order_by('name')
print(f'Inactive hosts: {inactive.count()}')
for h in inactive:
    print(f'  - {h.name} ({h.ip})')
"
```

---

**Fecha**: 17 de Octubre 2025  
**Versión**: Diaken 1.0  
**Estado**: ✅ Comando disponible - Listo para usar
