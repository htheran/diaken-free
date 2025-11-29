# Windows VM Deployment Asíncrono con Celery

**Fecha de Implementación:** 20 de Octubre 2025  
**Estado:** ✅ COMPLETADO Y FUNCIONANDO

---

## Resumen

Conversión exitosa del deployment de Windows VMs de **síncrono** a **asíncrono** usando Celery, logrando:

- ✅ Output en tiempo real (cada 5 líneas)
- ✅ Respuesta inmediata (<5 segundos)
- ✅ No bloquea el navegador
- ✅ Progress bar realista
- ✅ Consistencia total con Linux deployments
- ✅ 4 deployments paralelos posibles

---

## Arquitectura

### Flujo Completo

```
Usuario → Django View → Celery Task → Ansible → vCenter
   ↓          ↓              ↓           ↓          ↓
Frontend   Clone VM    8 Steps      Provision   Network
Polling    Power On    Async        VM Config   Change
```

### Componentes

1. **Frontend:** `templates/deploy/deploy_windows_vm_form.html`
   - Progress Area con barra de progreso
   - Output en tiempo real (ventana colapsable)
   - Polling AJAX cada 3 segundos
   - Timeout: 30 minutos (1800 polls)

2. **Django View:** `deploy/views_windows.py`
   - Clona VM en vCenter
   - Enciende VM
   - Crea DeploymentHistory
   - Despacha Celery task
   - Retorna JSON inmediatamente (<5s)

3. **Celery Task:** `deploy/tasks_windows.py`
   - 8 pasos con output incremental
   - Actualiza DB cada 5 líneas
   - subprocess.Popen() para captura en tiempo real
   - Timeout: 30 minutos (1800 segundos)

4. **Ansible Playbook:** `ansible/provision_windows_vm.yml`
   - Programa reinicio (40s)
   - Cambia hostname (PowerShell)
   - Configura IP estática
   - Playbook completa antes del reinicio

---

## Flujo de Deployment

### Paso 1: Django View (< 5 segundos)

```python
# deploy/views_windows.py
1. Validar formulario
2. Clonar VM en vCenter
3. Encender VM
4. Crear DeploymentHistory
5. Despachar Celery task
6. Retornar JSON con history_id
```

**Respuesta JSON:**
```json
{
  "success": true,
  "history_id": 123,
  "task_id": "abc-123-def",
  "message": "VM test-wind7 deployment started"
}
```

### Paso 2: Celery Task (8 pasos, ~5-10 minutos)

```python
# deploy/tasks_windows.py - provision_windows_vm_async()

Step 1: Boot wait (30s)
  - Espera que Windows arranque
  - VM en red de plantilla

Step 2: WinRM connectivity (6 retries)
  - Prueba conexión WinRM
  - Retry cada 10 segundos

Step 3: Ansible playbook (tiempo real)
  - Programa reinicio (40s)
  - Cambia hostname (PowerShell)
  - Configura IP estática
  - Playbook completa en ~10s
  - Output capturado línea por línea

Step 4: Shutdown wait (50s)
  - Espera que VM apague
  - Reinicio programado se ejecuta

Step 5: Network change in vCenter
  - VM apagado
  - Cambia red usando govc
  - Seguro cambiar red

Step 6: Power on VM
  - Enciende VM en nueva red

Step 7: Boot wait (60s)
  - Espera que Windows arranque
  - En nueva red

Step 8: Network validation
  - Valida conectividad en nueva IP
  - Registra VM en inventario
  - Envía notificación
```

### Paso 3: Frontend Polling

```javascript
// Polling cada 3 segundos
fetch('/deploy/history-status/' + historyId)
  .then(response => response.json())
  .then(data => {
    // Actualizar output
    outputElement.textContent = data.output;
    
    // Actualizar progreso
    progressBar.style.width = calculateProgress() + '%';
    
    // Verificar si terminó
    if (data.status === 'success' || data.status === 'failed') {
      stopPolling();
      showResult(data);
    }
  });
```

---

## Ansible Playbook

### Flujo del Playbook

```yaml
# ansible/provision_windows_vm.yml

1. Wait for WinRM (120s timeout)
2. Get current system info
3. Schedule reboot FIRST (40 seconds)
4. Change hostname (PowerShell - NO win_hostname)
5. Configure IP (netsh)
6. Playbook completa (~10 segundos)
```

**Por qué este orden funciona:**

- ✅ Reinicio programado al inicio (40s)
- ✅ Hostname e IP se configuran rápido (<10s)
- ✅ Playbook termina ANTES del reinicio
- ✅ VM reinicia automáticamente
- ✅ Celery cambia red mientras VM apagado
- ✅ Todo sincronizado perfectamente

### Cambio Crítico: PowerShell en lugar de win_hostname

**ANTES (❌ Causaba desconexión):**
```yaml
- name: Change hostname
  win_hostname:
    name: "{{ new_hostname }}"
  # ← WinRM se desconecta AQUÍ
```

**AHORA (✅ Mantiene conexión):**
```yaml
- name: Change hostname using PowerShell
  win_shell: |
    Rename-Computer -NewName "{{ new_hostname }}" -Force
  # ✅ WinRM sigue activo
```

**Razón:** `win_hostname` reinicia el servicio WinRM internamente, causando pérdida de conexión inmediata. PowerShell directo no tiene este problema.

---

## Archivos Modificados

### 1. deploy/tasks_windows.py (NUEVO - 438 líneas)

**Función Principal:**
```python
@shared_task(bind=True, time_limit=1800, soft_time_limit=1680)
def provision_windows_vm_async(
    self,
    history_id,
    template_ip,
    new_ip,
    new_hostname,
    gateway,
    dns1,
    dns2,
    vcenter_host,
    vcenter_user,
    vcenter_password,
    datacenter,
    cluster,
    network_name,
    windows_user,
    windows_password,
    windows_auth_type,
    windows_port,
    deploy_env,
    deploy_group,
    template_name
):
    # 8 pasos con output incremental
    # Actualiza DB cada 5 líneas
    # subprocess.Popen() para captura en tiempo real
```

**Características:**
- Time limit: 1800s (30 minutos)
- Soft time limit: 1680s (28 minutos)
- Output incremental cada 5 líneas
- Logging detallado: `[CELERY-WINDOWS-{task_id}]`
- Manejo de errores robusto

### 2. deploy/views_windows.py (MODIFICADO - 318 líneas)

**ANTES:** 688 líneas (todo síncrono)  
**DESPUÉS:** 318 líneas (370 líneas eliminadas)

**Cambios:**
- Eliminado código de provisioning síncrono
- Solo clona VM y despacha Celery
- Retorna JSON inmediatamente
- Import: `from deploy.tasks_windows import provision_windows_vm_async`

### 3. diaken/celery.py (MODIFICADO)

**Agregado:**
```python
# Explicitly import Windows deployment tasks
try:
    from deploy import tasks_windows
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f'Could not import deploy.tasks_windows: {e}')
```

**Razón:** Garantiza que Celery registre la tarea al iniciar.

### 4. ansible/provision_windows_vm.yml (MODIFICADO)

**Cambios:**
1. Reinicio programado al inicio (línea 35)
2. PowerShell en lugar de win_hostname (línea 45)
3. Configuración de IP sin cambiar DNS (línea 59)

---

## Configuración de Celery

### Tarea Registrada

```bash
$ celery -A diaken inspect registered | grep provision_windows_vm_async
    * deploy.tasks.provision_windows_vm_async
```

### Configuración

```python
# diaken/celery.py
app.conf.update(
    task_time_limit=1800,        # 30 minutos hard limit
    task_soft_time_limit=1680,   # 28 minutos soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
```

### Servicio Systemd

```ini
# /etc/systemd/system/celery-diaken.service
[Service]
User=apache
WorkingDirectory=/opt/www/app/diaken-pdn
ExecStart=/opt/www/app/diaken-pdn/venv/bin/celery -A diaken worker \
  --loglevel=info \
  --logfile=/var/log/celery/diaken-worker.log \
  --pidfile=/var/run/celery/diaken-worker.pid \
  --concurrency=4 \
  --max-tasks-per-child=50
```

**Estado:**
```bash
$ sudo systemctl status celery-diaken
● celery-diaken.service - Celery Worker for Diaken
   Active: active (running)
   Workers: 4
```

---

## Frontend

### Progress Area

```html
<!-- Visible durante ejecución -->
<div id="progressArea">
  <div class="progress-bar">23%</div>
  <p>Deployment started! Waiting for output...</p>
  <p>Time elapsed: 8m 25s</p>
  <button onclick="toggleOutput()">Show Real-time Output</button>
  <div id="outputContainer" style="display:none">
    <!-- Output en tiempo real -->
  </div>
</div>
```

### Result Area

```html
<!-- Visible al completar -->
<div id="resultArea" style="display:none">
  <div class="alert alert-success">
    <h4>Deployment Completed!</h4>
    <p>VM test-wind7 deployed successfully</p>
  </div>
  <pre id="finalOutput">
    <!-- Output completo -->
  </pre>
</div>
```

### JavaScript Polling

```javascript
function startDeploymentPolling(historyId) {
  const maxPolls = 1800;  // 30 minutos (1800 * 3s)
  let pollCount = 0;
  
  const pollInterval = setInterval(() => {
    pollCount++;
    
    fetch(`/deploy/history-status/${historyId}/`)
      .then(response => response.json())
      .then(data => {
        // Actualizar output
        updateOutput(data.output);
        
        // Actualizar progreso
        updateProgress(pollCount, maxPolls);
        
        // Verificar si terminó
        if (data.status === 'success' || data.status === 'failed') {
          clearInterval(pollInterval);
          showDeploymentResult(historyId);
        }
      });
  }, 3000);  // Cada 3 segundos
}
```

---

## Comparación: Antes vs Ahora

| Característica | Antes | Ahora |
|----------------|-------|-------|
| Ejecución | Síncrono | ✅ Asíncrono |
| Respuesta | 5-10 min | ✅ <5s |
| Output | De golpe | ✅ Tiempo real |
| Navegador | Bloqueado | ✅ No bloqueado |
| Paralelo | No | ✅ 4 deployments |
| Progress | No | ✅ Barra realista |
| Timeout | Frecuente | ✅ Nunca |
| Consistencia | ❌ | ✅ Igual a Linux |
| Código | 688 líneas | ✅ 318 líneas |

---

## Timeouts Configurados

| Componente | Timeout | Razón |
|------------|---------|-------|
| Celery Task | 30 min | Windows Updates + reinicios |
| Frontend Polling | 30 min | 1800 polls × 3s |
| WinRM Connection | 30s | Por tarea |
| Ansible Playbook | 10 min | Suficiente para provision |
| Boot Wait | 60s | Windows arranque |
| Shutdown Wait | 50s | Apagado completo |

---

## Verificación

### Comandos de Verificación

```bash
# 1. Verificar tarea registrada
celery -A diaken inspect registered | grep provision_windows_vm_async

# 2. Verificar sintaxis
python3 -m py_compile deploy/tasks_windows.py
python3 -m py_compile deploy/views_windows.py

# 3. Verificar servicios
sudo systemctl status celery-diaken
sudo systemctl status httpd

# 4. Ver logs en tiempo real
sudo tail -f /var/log/celery/diaken-worker.log | grep CELERY-WINDOWS

# 5. Verificar deployment
python manage.py shell -c "
from history.models import DeploymentHistory
d = DeploymentHistory.objects.order_by('-id').first()
print(f'Status: {d.status}, Target: {d.target}')
"
```

### Deployment Exitoso

```
Step 1/8: Waiting 30 seconds for Windows to boot...
✓ Boot wait completed

Step 2/8: Testing WinRM connectivity to 10.100.18.85...
✓ WinRM connection successful

Step 3/8: Running Ansible playbook...
PLAY [Customize Windows Server VM] *********************************************
TASK [Change hostname using PowerShell] ****************************************
changed: [10.100.18.85]
TASK [Configure static IP and gateway] *****************************************
changed: [10.100.18.85]
PLAY RECAP *********************************************************************
10.100.18.85 : ok=7 changed=3 unreachable=0 failed=0
✓ Ansible playbook completed successfully

Step 4/8: Waiting 50 seconds for VM to shutdown...
✓ Shutdown wait completed

Step 5/8: Changing network to dP3009 in vCenter...
✓ Network changed successfully

Step 6/8: Powering on VM...
✓ VM powered on

Step 7/8: Waiting 60 seconds for Windows to boot...
✓ Boot wait completed

Step 8/8: Validating network connectivity to 10.100.9.107...
✓ Network validation successful

✅ SUCCESS: Windows VM deployment completed
Hostname: test-wind7
IP: 10.100.9.107
Network: dP3009
Environment: PROVISIONAL
```

---

## Problemas Resueltos

### 1. Syntax Error en views_windows.py
**Problema:** `try:` sin `except:`  
**Solución:** Agregado bloque `except Exception as e`

### 2. Tarea No Registrada en Celery
**Problema:** `KeyError: 'deploy.tasks.provision_windows_vm_async'`  
**Solución:** Import explícito en `diaken/celery.py`

### 3. Import Incorrecto
**Problema:** `cannot import name 'provision_windows_vm_async' from 'deploy.tasks'`  
**Solución:** Import desde `deploy.tasks_windows`

### 4. win_hostname Desconecta WinRM
**Problema:** Timeout en todas las tareas después de cambiar hostname  
**Solución:** PowerShell directo con `Rename-Computer`

### 5. Orden de Ejecución
**Problema:** IP no cambiaba, red no cambiaba  
**Solución:** Shutdown al inicio, hostname e IP después

---

## Mejores Prácticas Aplicadas

1. ✅ **Separación de Responsabilidades**
   - Django: Clona VM y despacha
   - Celery: Provisioning completo
   - Frontend: Polling y display

2. ✅ **Output en Tiempo Real**
   - subprocess.Popen() en lugar de run()
   - Actualización cada 5 líneas
   - Performance optimizada

3. ✅ **Manejo de Errores Robusto**
   - Try/except en cada paso
   - ignore_errors en Ansible
   - Logging detallado

4. ✅ **Timeouts Apropiados**
   - 30 minutos para Celery
   - 30 segundos por conexión
   - 10 minutos para playbook

5. ✅ **Consistencia con Linux**
   - Mismo flujo asíncrono
   - Mismo frontend
   - Misma experiencia de usuario

6. ✅ **Código Limpio**
   - Sin print() statements
   - Sin logger.debug() en producción
   - Sin código muerto
   - Sin backups en git

---

## Estado Final

✅ **COMPLETADO Y FUNCIONANDO**

- Windows deployment ahora es asíncrono
- Output en tiempo real
- Consistente con Linux
- 370 líneas de código eliminadas
- Sin código de debugging
- Producción ready

**Fecha de Completación:** 20 de Octubre 2025  
**Commits:** 7 commits totales  
**Archivos Modificados:** 4  
**Archivos Nuevos:** 1  
**Líneas Eliminadas:** 370  
**Líneas Agregadas:** 438

---

## Mantenimiento

### Logs

```bash
# Celery worker logs
sudo tail -f /var/log/celery/diaken-worker.log

# Django logs
sudo tail -f /opt/www/logs/django.log

# Deployment logs
sudo tail -f /opt/www/logs/deployment.log
```

### Reiniciar Servicios

```bash
# Después de cambios en código
sudo systemctl restart celery-diaken
sudo systemctl restart httpd

# Verificar estado
sudo systemctl status celery-diaken
sudo systemctl status httpd
```

### Monitoreo

```bash
# Ver tareas activas
celery -A diaken inspect active

# Ver estadísticas
celery -A diaken inspect stats

# Ver workers
celery -A diaken inspect registered
```

---

## Contacto

Para preguntas o problemas, contactar al equipo de desarrollo.

**Última Actualización:** 20 de Octubre 2025
