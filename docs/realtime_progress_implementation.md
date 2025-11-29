# Implementación de Progreso en Tiempo Real con Celery

## Estado Actual

✅ **Infraestructura Celery**: Instalada y funcionando  
✅ **Endpoint AJAX**: Creado para consultar progreso  
⏳ **Integración en vistas**: Pendiente  
⏳ **JavaScript en frontend**: Pendiente actualizar  

## Componentes Implementados

### 1. Tarea Celery con Progreso (`deploy/tasks_deployment.py`)

```python
@shared_task(bind=True, name='deploy.tasks.deploy_vm_async')
def deploy_vm_async(self, history_id, deployment_params):
    # Reportar progreso en cada paso
    self.update_state(
        state='PROGRESS',
        meta={
            'current_step': 1,
            'total_steps': 8,
            'percent': 12,
            'message': 'Connecting to vCenter...',
            'status': 'running'
        }
    )
    # ... ejecutar paso ...
```

**Características**:
- Usa `self.update_state()` para reportar progreso
- Estado `PROGRESS` con metadata personalizada
- 8 pasos predefinidos del deployment
- Logging detallado en cada paso

### 2. Endpoint AJAX (`deploy/ajax.py`)

```python
@login_required
def get_task_progress(request, task_id):
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    # Retorna JSON con estado actual
    return JsonResponse({
        'task_id': task_id,
        'state': task.state,
        'status': 'running',
        'current_step': 3,
        'total_steps': 8,
        'percent': 37,
        'message': 'Powering on VM...'
    })
```

**URL**: `/deploy/ajax/task-progress/<task_id>/`

### 3. Estados de la Tarea

| Estado | Descripción | Progreso |
|--------|-------------|----------|
| `PENDING` | Esperando iniciar | 0% |
| `PROGRESS` | Ejecutando (con progreso) | 1-99% |
| `SUCCESS` | Completado exitosamente | 100% |
| `FAILURE` | Falló con error | 0% |

## Pasos para Integrar

### Paso 1: Modificar la Vista de Deployment

Actualmente en `deploy/views.py`, el deployment es síncrono:

```python
# ANTES (Síncrono)
def deploy_vm(request):
    if request.method == 'POST':
        # ... validación ...
        
        # Ejecutar deployment (bloquea 3-10 minutos)
        result = execute_deployment_sync(...)
        
        messages.success(request, 'Deployment completed')
        return redirect('history:history_list')
```

Cambiar a:

```python
# DESPUÉS (Asíncrono con Celery)
def deploy_vm(request):
    if request.method == 'POST':
        # ... validación ...
        
        # Crear registro de historial
        history = DeploymentHistory.objects.create(
            user=request.user,
            target=hostname,
            status='pending',
            # ... otros campos ...
        )
        
        # Encolar tarea asíncrona
        from deploy.tasks_deployment import deploy_vm_async
        task = deploy_vm_async.delay(
            history_id=history.pk,
            deployment_params={
                'vcenter_host': vcenter_host,
                'hostname': hostname,
                # ... otros parámetros ...
            }
        )
        
        # Guardar task ID
        history.celery_task_id = task.id
        history.save()
        
        # Retornar task ID al frontend
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'history_id': history.pk,
            'message': 'Deployment started'
        })
```

### Paso 2: Actualizar el JavaScript del Frontend

Reemplazar `simulateProgress()` con progreso real:

```javascript
// ANTES: Progreso simulado
function simulateProgress() {
    const steps = [
        { step: 1, percent: 12, message: 'Connecting...', delay: 2000 },
        { step: 2, percent: 25, message: 'Cloning...', delay: 15000 },
        // ... tiempos estimados ...
    ];
    // Actualizar UI con tiempos fijos
}

// DESPUÉS: Progreso real desde Celery
function checkRealProgress(taskId) {
    $.ajax({
        url: `/deploy/ajax/task-progress/${taskId}/`,
        method: 'GET',
        success: function(data) {
            // Actualizar UI con progreso real
            $('#progressBar').css('width', data.percent + '%');
            $('#progressPercent').text(data.percent + '%');
            $('#progressMessage').html(`<strong>Step ${data.current_step}/${data.total_steps}:</strong> ${data.message}`);
            
            // Marcar paso como completado
            $(`#step${data.current_step} i`)
                .removeClass('text-muted fa-circle')
                .addClass('text-success fa-check-circle');
            
            // Si no ha terminado, seguir consultando
            if (data.status === 'running' || data.status === 'pending') {
                setTimeout(() => checkRealProgress(taskId), 1000);  // Cada 1 segundo
            } else if (data.status === 'success') {
                // Deployment completado
                $('#progressBar').removeClass('progress-bar-animated').addClass('bg-success');
                $('#progressMessage').html('<strong><i class="fas fa-check-circle text-success"></i> Deployment Completed!</strong>');
                setTimeout(() => {
                    window.location.href = `/history/${data.history_id}/`;
                }, 2000);
            } else if (data.status === 'failed') {
                // Deployment falló
                $('#progressBar').removeClass('progress-bar-animated').addClass('bg-danger');
                $('#progressMessage').html(`<strong><i class="fas fa-times-circle text-danger"></i> Failed: ${data.message}</strong>`);
            }
        },
        error: function() {
            console.error('Error checking task progress');
            setTimeout(() => checkRealProgress(taskId), 2000);  // Reintentar
        }
    });
}
```

### Paso 3: Modificar el Submit del Formulario

```javascript
$('#deployForm').submit(function(e) {
    e.preventDefault();  // Prevenir submit normal
    
    // Mostrar modal de progreso
    $('#progressModal').modal('show');
    
    // Enviar formulario via AJAX
    $.ajax({
        url: $(this).attr('action'),
        method: 'POST',
        data: $(this).serialize(),
        success: function(response) {
            if (response.success) {
                // Iniciar polling de progreso
                checkRealProgress(response.task_id);
            } else {
                alert('Error: ' + response.message);
                $('#progressModal').modal('hide');
            }
        },
        error: function() {
            alert('Error submitting form');
            $('#progressModal').modal('hide');
        }
    });
});
```

## Ejemplo Completo de Flujo

### 1. Usuario Submit Formulario

```
Usuario → Click "Deploy VM" → AJAX POST
```

### 2. Vista Crea Tarea y Responde

```python
# Vista responde inmediatamente con task_id
{
    "success": true,
    "task_id": "abc123-def456-ghi789",
    "history_id": 325
}
```

### 3. JavaScript Inicia Polling

```javascript
// Consulta cada 1 segundo
setInterval(() => {
    GET /deploy/ajax/task-progress/abc123-def456-ghi789/
}, 1000);
```

### 4. Celery Worker Reporta Progreso

```python
# Paso 1
self.update_state(state='PROGRESS', meta={
    'current_step': 1,
    'total_steps': 8,
    'percent': 12,
    'message': 'Connecting to vCenter...'
})

# Paso 2
self.update_state(state='PROGRESS', meta={
    'current_step': 2,
    'total_steps': 8,
    'percent': 25,
    'message': 'Cloning VM from template...'
})

# ... etc ...
```

### 5. Frontend Actualiza UI en Tiempo Real

```
Barra de progreso: 12% → 25% → 37% → ... → 100%
Mensaje: "Step 1/8: Connecting..." → "Step 2/8: Cloning..." → ...
Checkmarks: ✓ Step 1 → ✓ Step 2 → ✓ Step 3 → ...
```

### 6. Deployment Completa

```python
# Celery worker termina
return {
    'status': 'success',
    'message': 'VM deployed successfully',
    'percent': 100
}
```

### 7. Redirect Automático

```javascript
// JavaScript detecta success y redirige
window.location.href = '/history/325/';
```

## Ventajas del Progreso Real vs Simulado

| Característica | Simulado (Actual) | Real (Con Celery) |
|----------------|-------------------|-------------------|
| Precisión | ❌ Estimado | ✅ Exacto |
| Tiempo real | ❌ Tiempos fijos | ✅ Progreso real |
| Errores | ❌ No detecta | ✅ Detecta inmediatamente |
| Pasos lentos | ❌ No se nota | ✅ Se ve en tiempo real |
| Múltiples deployments | ❌ No soporta | ✅ Cada uno independiente |
| Navegador bloqueado | ❌ Sí (síncrono) | ✅ No (asíncrono) |

## Testing

### Probar la Tarea Manualmente

```python
# En Django shell
from deploy.tasks_deployment import deploy_vm_async

# Encolar tarea
task = deploy_vm_async.delay(
    history_id=325,
    deployment_params={'test': True}
)

# Ver task ID
print(f"Task ID: {task.id}")

# Consultar progreso
from celery.result import AsyncResult
result = AsyncResult(task.id)
print(f"State: {result.state}")
print(f"Info: {result.info}")
```

### Probar el Endpoint AJAX

```bash
# Obtener task ID de un deployment
curl http://localhost/deploy/ajax/task-progress/abc123-def456-ghi789/

# Respuesta:
{
    "task_id": "abc123-def456-ghi789",
    "state": "PROGRESS",
    "status": "running",
    "current_step": 3,
    "total_steps": 8,
    "percent": 37,
    "message": "Powering on VM..."
}
```

## Próximos Pasos

1. ⏳ **Mover lógica de deployment** de `deploy/views.py` a `deploy/tasks_deployment.py`
2. ⏳ **Actualizar vista** para usar tarea asíncrona
3. ⏳ **Modificar JavaScript** para usar progreso real
4. ⏳ **Probar deployment completo** end-to-end
5. ⏳ **Agregar manejo de errores** robusto
6. ⏳ **Implementar para Windows** deployments también

## Archivos Creados/Modificados

- ✅ `deploy/tasks_deployment.py` - Tarea con progreso
- ✅ `deploy/ajax.py` - Endpoint de progreso
- ✅ `deploy/urls.py` - URL del endpoint
- ⏳ `deploy/views.py` - Modificar para usar Celery
- ⏳ `templates/deploy/deploy_vm_form.html` - Actualizar JavaScript

## Referencias

- [Celery Task States](https://docs.celeryproject.org/en/stable/userguide/tasks.html#task-states)
- [Custom Task States](https://docs.celeryproject.org/en/stable/userguide/tasks.html#custom-states)
- [AsyncResult API](https://docs.celeryproject.org/en/stable/reference/celery.result.html)

---

**Fecha**: 17 de Octubre 2025  
**Estado**: ✅ Infraestructura lista - ⏳ Integración pendiente  
**Próximo paso**: Mover lógica de deployment a tarea Celery
