# Implementación de Celery para Tareas Asíncronas - Oct 17, 2025

## Descripción

Celery ha sido implementado para ejecutar tareas de deployment y ejecución de playbooks de forma asíncrona, evitando que el navegador se quede "colgado" esperando respuesta.

## Componentes Instalados

### 1. Dependencias Python
```bash
celery==5.5.3
redis==6.4.0
billiard==4.2.2
kombu==5.5.4
vine==5.1.0
click==8.3.0
amqp==5.3.1
```

### 2. Redis (Message Broker)
- **Versión**: 6.2.19
- **Puerto**: 6379
- **Servicio**: `redis.service`
- **Estado**: Habilitado y ejecutándose

### 3. Celery Worker
- **Servicio**: `celery-diaken.service`
- **Usuario**: apache
- **Concurrency**: 4 workers
- **Max tasks per child**: 50
- **Estado**: Habilitado y ejecutándose

## Archivos Creados/Modificados

### Archivos de Configuración

1. **`/opt/www/app/diaken-pdn/diaken/celery.py`**
   - Configuración principal de Celery
   - Autodiscovery de tareas

2. **`/opt/www/app/diaken-pdn/diaken/__init__.py`**
   - Importación de Celery app
   - Asegura que Celery se cargue con Django

3. **`/opt/www/app/diaken-pdn/diaken/settings.py`**
   - Configuración de Celery:
     ```python
     CELERY_BROKER_URL = 'redis://localhost:6379/0'
     CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
     CELERY_TIMEZONE = 'America/Bogota'
     CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
     ```

4. **`/opt/www/app/diaken-pdn/deploy/tasks.py`**
   - Tareas asíncronas de Celery:
     * `execute_playbook_async`: Ejecutar playbook individual
     * `execute_group_playbook_async`: Ejecutar playbook en grupo de hosts

5. **`/etc/systemd/system/celery-diaken.service`**
   - Servicio systemd para Celery worker
   - Configurado para iniciar automáticamente

### Directorios Creados

```bash
/var/log/celery/          # Logs de Celery (owner: apache)
/var/run/celery/          # PID files (owner: apache)
```

## Configuración de Celery

### Broker y Backend
- **Broker**: Redis en `localhost:6379/0`
- **Result Backend**: Redis en `localhost:6379/0`
- **Serializer**: JSON
- **Timezone**: America/Bogota

### Workers
- **Concurrency**: 4 workers paralelos
- **Max tasks per child**: 50 (reinicia worker después de 50 tareas)
- **Time limit**: 30 minutos por tarea
- **Soft time limit**: 25 minutos

## Tareas Disponibles

### 1. `execute_playbook_async`
Ejecuta un playbook de forma asíncrona.

**Parámetros**:
- `history_id`: ID del registro DeploymentHistory

**Uso**:
```python
from deploy.tasks import execute_playbook_async

# Encolar tarea
task = execute_playbook_async.delay(history_id=123)

# Obtener resultado
result = task.get(timeout=10)
```

### 2. `execute_group_playbook_async`
Ejecuta un playbook en un grupo de hosts de forma asíncrona.

**Parámetros**:
- `history_id`: ID del registro DeploymentHistory
- `host_ids`: Lista de IDs de hosts
- `playbook_id`: ID del playbook a ejecutar

**Uso**:
```python
from deploy.tasks import execute_group_playbook_async

# Encolar tarea
task = execute_group_playbook_async.delay(
    history_id=123,
    host_ids=[1, 2, 3, 4, 5],
    playbook_id=10
)

# Obtener resultado
result = task.get(timeout=10)
```

## Variables de Entorno para Ansible

Las tareas de Celery incluyen las siguientes variables de entorno para evitar problemas de permisos:

```python
ansible_env = {
    'ANSIBLE_LOCAL_TEMP': '/tmp/ansible-local',
    'ANSIBLE_REMOTE_TEMP': '~/.ansible/tmp',
    'HOME': '/tmp',
    'ANSIBLE_SSH_CONTROL_PATH_DIR': '/tmp/ansible-ssh',
    'ANSIBLE_HOME_DIR': '/tmp',
    'ANSIBLE_HOST_KEY_CHECKING': 'False'
}
```

## Gestión de Servicios

### Redis
```bash
# Iniciar
sudo systemctl start redis

# Detener
sudo systemctl stop redis

# Reiniciar
sudo systemctl restart redis

# Ver estado
sudo systemctl status redis

# Ver logs
sudo journalctl -xeu redis.service
```

### Celery Worker
```bash
# Iniciar
sudo systemctl start celery-diaken

# Detener
sudo systemctl stop celery-diaken

# Reiniciar
sudo systemctl restart celery-diaken

# Ver estado
sudo systemctl status celery-diaken

# Ver logs
sudo tail -f /var/log/celery/diaken-worker.log

# Ver logs de systemd
sudo journalctl -xeu celery-diaken.service -f
```

## Monitoreo

### Ver tareas en ejecución
```bash
# Conectar a Celery
source /opt/www/app/diaken-pdn/venv/bin/activate
cd /opt/www/app/diaken-pdn

# Ver workers activos
celery -A diaken inspect active

# Ver tareas registradas
celery -A diaken inspect registered

# Ver estadísticas
celery -A diaken inspect stats

# Ver cola de tareas
celery -A diaken inspect reserved
```

### Ver estado de Redis
```bash
# Conectar a Redis CLI
redis-cli

# Ver todas las keys
KEYS *

# Ver longitud de cola
LLEN celery

# Ver info
INFO

# Salir
EXIT
```

## Flujo de Ejecución Asíncrona

### Antes (Síncrono)
```
Usuario → Submit Form → Django View → Ansible (3-10 min) → Response → Usuario
                         ↑_______________ BLOQUEADO _______________↑
```

### Después (Asíncrono)
```
Usuario → Submit Form → Django View → Celery Task (encolada)
                            ↓
                      Response inmediata
                            ↓
                      Redirect a History
                            ↓
                      AJAX polling
                            ↓
                      Actualiza status

Celery Worker → Ejecuta Ansible → Actualiza DB → Usuario ve resultado
```

## Beneficios

1. **✅ No más navegador colgado**
   - Respuesta inmediata al usuario
   - Redirect a página de historial

2. **✅ Múltiples deployments en paralelo**
   - 4 workers pueden ejecutar 4 tareas simultáneamente
   - Ideal para grupos de 20+ servidores

3. **✅ Mejor experiencia de usuario**
   - Usuario puede ver el progreso
   - No hay timeouts de Apache

4. **✅ Escalabilidad**
   - Fácil agregar más workers
   - Distribución de carga automática

5. **✅ Confiabilidad**
   - Reintentos automáticos
   - Persistencia de tareas en Redis
   - Workers se reinician automáticamente

## Próximos Pasos

### 1. Integrar Celery en las vistas existentes

Modificar las vistas para usar tareas asíncronas:

```python
# En deploy/views.py
from deploy.tasks import execute_group_playbook_async

def execute_playbook(request):
    # ... validación ...
    
    # Crear registro de historial
    history_record = DeploymentHistory.objects.create(...)
    
    # Encolar tarea asíncrona
    task = execute_group_playbook_async.delay(
        history_id=history_record.pk,
        host_ids=host_ids,
        playbook_id=playbook_id
    )
    
    # Guardar task ID en el historial
    history_record.celery_task_id = task.id
    history_record.save()
    
    # Redirect inmediatamente
    messages.success(request, 'Deployment iniciado. Ver progreso en historial.')
    return redirect('history:detail', pk=history_record.pk)
```

### 2. Implementar AJAX polling en la página de historial

```javascript
// En history/detail.html
function checkTaskStatus() {
    $.ajax({
        url: '/history/{{ history.pk }}/status/',
        success: function(data) {
            if (data.status === 'running') {
                // Actualizar UI con progreso
                setTimeout(checkTaskStatus, 2000);  // Poll cada 2 segundos
            } else {
                // Tarea completada, recargar página
                location.reload();
            }
        }
    });
}

// Iniciar polling si la tarea está en ejecución
if (taskStatus === 'running') {
    checkTaskStatus();
}
```

### 3. Agregar campo celery_task_id al modelo DeploymentHistory

```python
# En history/models.py
class DeploymentHistory(models.Model):
    # ... campos existentes ...
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
```

### 4. Implementar Flower para monitoreo web

```bash
# Instalar Flower
pip install flower

# Ejecutar Flower
celery -A diaken flower --port=5555

# Acceder a http://localhost:5555
```

## Troubleshooting

### Worker no inicia
```bash
# Ver logs
sudo journalctl -xeu celery-diaken.service

# Verificar permisos
ls -la /var/log/celery /var/run/celery

# Verificar que Redis está corriendo
sudo systemctl status redis
```

### Tareas no se ejecutan
```bash
# Verificar conexión a Redis
redis-cli ping

# Ver workers activos
celery -A diaken inspect active

# Ver cola de tareas
celery -A diaken inspect reserved
```

### Error de permisos
```bash
# Asegurar que apache es el owner
sudo chown -R apache:apache /var/log/celery /var/run/celery

# Verificar permisos de /tmp
ls -la /tmp/ansible-*
```

## Referencias

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django + Celery Integration](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Monitoring](https://flower.readthedocs.io/)

## Estado

✅ **IMPLEMENTADO** - Celery configurado y funcionando

**Servicios activos**:
- ✅ Redis: `redis.service`
- ✅ Celery Worker: `celery-diaken.service` (4 workers)
- ✅ Apache/Django: `httpd.service`

**Próximo paso**: Integrar tareas asíncronas en las vistas de deployment
