# Guía de Deployment Asíncrono con Celery

## Resumen

Esta guía explica cómo funciona el sistema de deployments asíncronos implementado con Celery, que permite ejecutar tareas largas en background sin bloquear el navegador.

## Flujo Completo de Deployment Asíncrono

### 1. Usuario Envía Formulario
```
Usuario → Submit Form → Django View
```

### 2. Vista Crea Registro y Encola Tarea
```python
# En la vista de deployment
from deploy.tasks import execute_deployment_async

# Crear registro en historial con status='pending'
history_record = DeploymentHistory.objects.create(
    user=request.user,
    target=hostname,
    playbook='provision_vm.yml',
    status='pending',  # Estado inicial
    # ... otros campos ...
)

# Encolar tarea asíncrona en Celery
task = execute_deployment_async.delay(
    history_id=history_record.pk,
    # ... parámetros del deployment ...
)

# Guardar task ID para tracking
history_record.celery_task_id = task.id
history_record.save()

# Redirect inmediatamente (NO esperar)
messages.success(request, f'Deployment iniciado para {hostname}. Ver progreso en historial.')
return redirect('history:history_detail', pk=history_record.pk)
```

### 3. Usuario es Redirigido al Historial
```
Usuario ve página de historial inmediatamente
Status: "Pending" o "Running"
```

### 4. Celery Worker Ejecuta la Tarea en Background
```python
# En deploy/tasks.py
@shared_task(bind=True)
def execute_deployment_async(self, history_id, ...):
    # Actualizar status a 'running'
    history = DeploymentHistory.objects.get(pk=history_id)
    history.status = 'running'
    history.save()
    
    # Ejecutar deployment (Ansible, govc, etc.)
    # ... código de deployment ...
    
    # Actualizar status final
    history.status = 'success' or 'failed'
    history.completed_at = timezone.now()
    history.save()
```

### 5. AJAX Polling Actualiza la Página Automáticamente
```javascript
// En history_detail.html
// Polling cada 2 segundos
setInterval(function() {
    fetch('/history/<id>/status/')
        .then(response => response.json())
        .then(data => {
            if (data.status !== current_status) {
                location.reload();  // Recargar cuando cambie
            }
        });
}, 2000);
```

## Componentes Implementados

### 1. Modelo DeploymentHistory
```python
# history/models.py
class DeploymentHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),    # NUEVO
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)  # NUEVO
    # ... otros campos ...
```

### 2. Vista de Estado (AJAX)
```python
# history/views.py
@login_required
def check_task_status(request, pk):
    """Vista AJAX para verificar estado de tarea"""
    deployment = get_object_or_404(DeploymentHistory, pk=pk)
    
    response_data = {
        'status': deployment.status,
        'created_at': deployment.created_at.isoformat(),
        'completed_at': deployment.completed_at.isoformat() if deployment.completed_at else None,
        'duration': deployment.duration(),
    }
    
    if deployment.celery_task_id:
        task = AsyncResult(deployment.celery_task_id)
        response_data['celery_status'] = task.state
    
    return JsonResponse(response_data)
```

### 3. URL para AJAX
```python
# history/urls.py
urlpatterns = [
    path('<int:pk>/status/', views.check_task_status, name='check_task_status'),
]
```

### 4. Template con AJAX Polling
```html
<!-- templates/history/history_detail.html -->
{% if deployment.status == 'pending' or deployment.status == 'running' %}
<script>
(function() {
  function checkTaskStatus() {
    fetch('{% url "history:check_task_status" deployment.pk %}')
      .then(response => response.json())
      .then(data => {
        if (data.status !== '{{ deployment.status }}') {
          location.reload();  // Recargar cuando cambie
        }
      });
  }
  
  // Polling cada 2 segundos
  setInterval(checkTaskStatus, 2000);
  checkTaskStatus();  // Primera verificación inmediata
})();
</script>
{% endif %}
```

## Ejemplo de Uso: Convertir Vista Síncrona a Asíncrona

### Antes (Síncrono - Bloquea el navegador)
```python
def deploy_vm(request):
    if request.method == 'POST':
        # ... validación ...
        
        # Crear VM (30-60s)
        create_vm_in_vcenter(...)
        
        # Provisioning (30-60s)
        run_ansible_playbook(...)
        
        # Cambio de red (5-10s)
        change_network(...)
        
        # Total: 3-10 minutos bloqueando el navegador
        
        messages.success(request, 'Deployment completado')
        return redirect('history:history_list')
```

### Después (Asíncrono - Respuesta inmediata)
```python
def deploy_vm(request):
    if request.method == 'POST':
        # ... validación ...
        
        # Crear registro con status='pending'
        history = DeploymentHistory.objects.create(
            status='pending',
            # ... campos ...
        )
        
        # Encolar tarea asíncrona
        from deploy.tasks import deploy_vm_async
        task = deploy_vm_async.delay(
            history_id=history.pk,
            # ... parámetros ...
        )
        
        history.celery_task_id = task.id
        history.save()
        
        # Redirect INMEDIATAMENTE (< 1 segundo)
        messages.success(request, f'Deployment iniciado. Ver progreso en historial.')
        return redirect('history:history_detail', pk=history.pk)
```

### Tarea Celery
```python
# deploy/tasks.py
@shared_task(bind=True, name='deploy.tasks.deploy_vm_async')
def deploy_vm_async(self, history_id, vcenter_host, hostname, ...):
    try:
        history = DeploymentHistory.objects.get(pk=history_id)
        history.status = 'running'
        history.save()
        
        # Crear VM (30-60s)
        create_vm_in_vcenter(...)
        
        # Provisioning (30-60s)
        output = run_ansible_playbook(...)
        
        # Cambio de red (5-10s)
        change_network(...)
        
        # Éxito
        history.status = 'success'
        history.ansible_output = output
        history.completed_at = timezone.now()
        history.save()
        
        return {'status': 'success'}
        
    except Exception as e:
        history.status = 'failed'
        history.ansible_output = f"Error: {str(e)}"
        history.completed_at = timezone.now()
        history.save()
        
        return {'status': 'error', 'message': str(e)}
```

## Beneficios del Sistema Asíncrono

### 1. Experiencia de Usuario
- ✅ **Respuesta inmediata** (< 1 segundo)
- ✅ **No más navegador colgado**
- ✅ **Actualización automática** del progreso
- ✅ **Usuario puede navegar** mientras se ejecuta

### 2. Escalabilidad
- ✅ **4 deployments simultáneos** (4 workers)
- ✅ **Ideal para grupos de 20+ servidores**
- ✅ **Fácil escalar** (agregar más workers)
- ✅ **Distribución automática** de carga

### 3. Confiabilidad
- ✅ **Persistencia** de tareas en Redis
- ✅ **Reintentos automáticos** (configurable)
- ✅ **Workers se reinician** automáticamente
- ✅ **Logs detallados** en `/var/log/celery/`

### 4. Performance
- ✅ **Sin timeouts de Apache**
- ✅ **Múltiples tareas en paralelo**
- ✅ **Mejor uso de recursos**
- ✅ **No bloquea threads de Django**

## Monitoreo y Troubleshooting

### Ver Estado de Workers
```bash
# Ver workers activos
celery -A diaken inspect active

# Ver estadísticas
celery -A diaken inspect stats

# Ver tareas registradas
celery -A diaken inspect registered
```

### Ver Logs
```bash
# Logs de Celery worker
sudo tail -f /var/log/celery/diaken-worker.log

# Logs de systemd
sudo journalctl -xeu celery-diaken.service -f

# Logs de Django/Apache
sudo journalctl -xeu httpd.service -f
```

### Ver Cola de Tareas en Redis
```bash
redis-cli

# Ver longitud de cola
LLEN celery

# Ver todas las keys
KEYS *

# Ver info
INFO
```

### Reiniciar Workers
```bash
# Reiniciar servicio
sudo systemctl restart celery-diaken

# Reload (sin interrumpir tareas)
sudo systemctl reload celery-diaken

# Ver estado
sudo systemctl status celery-diaken
```

## Configuración Avanzada

### Aumentar Número de Workers
```bash
# Editar servicio
sudo nano /etc/systemd/system/celery-diaken.service

# Cambiar --concurrency=4 a --concurrency=8
ExecStart=/opt/www/app/diaken-pdn/venv/bin/celery -A diaken worker \
    --concurrency=8 \
    ...

# Recargar y reiniciar
sudo systemctl daemon-reload
sudo systemctl restart celery-diaken
```

### Configurar Reintentos
```python
# En deploy/tasks.py
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True
)
def deploy_vm_async(self, history_id, ...):
    # ... código ...
```

### Configurar Prioridades
```python
# Tarea de alta prioridad
task = deploy_vm_async.apply_async(
    args=[history_id, ...],
    priority=9  # 0-9, 9 es más alta
)

# Tarea de baja prioridad
task = cleanup_task.apply_async(
    args=[...],
    priority=1
)
```

## Próximos Pasos

### Implementaciones Pendientes

1. **Convertir deploy_vm a asíncrono**
   - Crear `deploy_vm_async` en `deploy/tasks.py`
   - Modificar `deploy/views.py` para usar tarea asíncrona
   - Probar deployment completo

2. **Convertir execute_playbook a asíncrono**
   - Ya existe `execute_playbook_async` en `deploy/tasks.py`
   - Modificar vistas para usar tarea asíncrona

3. **Convertir execute_group_playbook a asíncrono**
   - Ya existe `execute_group_playbook_async` en `deploy/tasks.py`
   - Modificar vistas para usar tarea asíncrona

4. **Agregar barra de progreso**
   - Usar `self.update_state()` en tareas
   - Mostrar progreso en tiempo real en UI

5. **Instalar Flower (opcional)**
   ```bash
   pip install flower
   celery -A diaken flower --port=5555
   # Acceder a http://localhost:5555
   ```

## Referencias

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django + Celery](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Monitoring](https://flower.readthedocs.io/)

## Estado Actual

✅ **Infraestructura Completa**:
- Celery instalado y configurado
- Redis funcionando
- Workers activos (4 workers)
- Modelo actualizado con `celery_task_id`
- Vista AJAX para verificar estado
- Template con polling automático

⏳ **Pendiente**:
- Convertir vistas existentes para usar tareas asíncronas
- Probar flujo completo end-to-end

---

**Fecha**: 17 de Octubre 2025  
**Versión**: Diaken 1.0 + Celery Async  
**Estado**: ✅ INFRAESTRUCTURA LISTA - Listo para integrar en vistas
