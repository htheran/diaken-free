# Optimización de Timeouts de Deployment - Oct 17, 2025

## Problema Reportado
El servidor se "colgaba" durante los deployments, dejando al navegador esperando sin respuesta.

## Diagnóstico

### Problema 1: Timeouts muy largos en Apache
```apache
socket-timeout=900      # 15 minutos
connect-timeout=900     # 15 minutos
request-timeout=900     # 15 minutos
queue-timeout=900       # 15 minutos
graceful-timeout=900    # 15 minutos
```

**Impacto**: El navegador esperaba hasta 15 minutos sin recibir respuesta, causando la sensación de que el servidor estaba "colgado".

### Problema 2: Tiempos de espera excesivos en el código
```python
time.sleep(60)   # Espera inicial para que VM arranque
time.sleep(90)   # Espera para reinicio (x2 veces)
# Total: 60 + 90 + 90 = 240 segundos (4 minutos) solo en sleeps
```

**Impacto**: Sumado a las operaciones de vCenter, Ansible y govc, el deployment total podía tomar más de 5-6 minutos, bloqueando el navegador.

### Problema 3: Deployment síncrono
El deployment se ejecuta de forma **síncrona**, bloqueando el thread de Apache/WSGI hasta que termine completamente.

## Soluciones Implementadas

### 1. ✅ Reducción de timeouts de Apache

**Archivo**: `/etc/httpd/conf.d/00-diaken-global.conf`

**Cambios**:
```apache
# ANTES (15 minutos)
socket-timeout=900
connect-timeout=900
request-timeout=900
queue-timeout=900
graceful-timeout=900

# DESPUÉS (5 minutos)
socket-timeout=300
connect-timeout=300
request-timeout=300
queue-timeout=300
graceful-timeout=300
```

**Beneficio**: 
- Timeouts más razonables (5 minutos)
- El navegador no se queda esperando indefinidamente
- Si un deployment tarda más de 5 minutos, se mostrará un error de timeout en lugar de quedarse colgado

### 2. ✅ Optimización de tiempos de espera

**Archivo**: `/opt/www/app/diaken-pdn/deploy/views.py`

**Cambios**:

| Operación | Antes | Después | Ahorro |
|-----------|-------|---------|--------|
| Espera inicial VM | 60s | 30s | -30s |
| Espera reinicio (éxito) | 90s | 60s | -30s |
| Espera reinicio (error) | 90s | 60s | -30s |
| **TOTAL** | **240s** | **150s** | **-90s (37% más rápido)** |

**Código modificado**:
```python
# Espera inicial reducida
time.sleep(30)  # Antes: 60

# Espera de reinicio reducida
time.sleep(60)  # Antes: 90
```

**Beneficio**:
- Deployment 90 segundos más rápido
- Menor probabilidad de timeout
- Mejor experiencia de usuario

### 3. 📋 Recomendación: Implementar deployment asíncrono (futuro)

**Problema actual**: El deployment es síncrono y bloquea el navegador.

**Solución recomendada**: Usar **Celery** o **threading** para ejecutar deployments en background.

**Flujo propuesto**:
1. Usuario envía formulario de deployment
2. Se crea registro en `DeploymentHistory` con status='pending'
3. Se inicia tarea en background
4. Usuario es redirigido inmediatamente al historial
5. La página de historial se actualiza automáticamente (AJAX polling o WebSockets)
6. Cuando el deployment termina, se actualiza el status a 'success' o 'failed'

**Beneficios**:
- ✅ Navegador nunca se queda colgado
- ✅ Usuario puede ver el progreso en tiempo real
- ✅ Múltiples deployments pueden ejecutarse en paralelo
- ✅ No hay timeouts de Apache

## Tiempos de Deployment Estimados

### Antes de las optimizaciones:
```
1. Crear VM en vCenter: ~30-60s
2. Espera inicial: 60s
3. Provisioning (Ansible): ~30-60s
4. Cambio de red (govc): ~5-10s
5. Espera reinicio: 90s
6. Verificación SSH: ~10-30s
7. Playbooks adicionales: ~30-120s (variable)

TOTAL: ~255-430 segundos (4-7 minutos)
```

### Después de las optimizaciones:
```
1. Crear VM en vCenter: ~30-60s
2. Espera inicial: 30s ⚡ (-30s)
3. Provisioning (Ansible): ~30-60s
4. Cambio de red (govc): ~5-10s
5. Espera reinicio: 60s ⚡ (-30s)
6. Verificación SSH: ~10-30s
7. Playbooks adicionales: ~30-120s (variable)

TOTAL: ~195-370 segundos (3-6 minutos) ⚡ (-60s promedio)
```

## Archivos Modificados

1. **`/etc/httpd/conf.d/00-diaken-global.conf`**:
   - Timeouts reducidos de 900s a 300s

2. **`/opt/www/app/diaken-pdn/deploy/views.py`**:
   - Espera inicial: 60s → 30s
   - Espera reinicio: 90s → 60s (2 lugares)

## Verificación

### Comprobar timeouts de Apache:
```bash
grep -E "(socket|connect|request|queue|graceful)-timeout" /etc/httpd/conf.d/00-diaken-global.conf
```

Debe mostrar:
```
socket-timeout=300
connect-timeout=300
request-timeout=300
queue-timeout=300
graceful-timeout=300
```

### Comprobar tiempos de espera en código:
```bash
grep "time.sleep" /opt/www/app/diaken-pdn/deploy/views.py
```

Debe mostrar:
```python
time.sleep(30)  # Espera inicial
time.sleep(60)  # Espera reinicio (2 veces)
```

## Monitoreo

### Ver logs de deployment en tiempo real:
```bash
sudo journalctl -xeu httpd.service -f | grep -E "(ANSIBLE|GOVC|NETWORK_CHANGE|POST_REBOOT)"
```

### Ver procesos WSGI activos:
```bash
ps aux | grep "wsgi:diaken"
```

### Ver uso de recursos:
```bash
top -b -n 1 | grep -E "(httpd|wsgi|python)"
```

## Estado
✅ **OPTIMIZADO** - Timeouts reducidos y tiempos de espera optimizados

## Próximos Pasos Recomendados

1. **Implementar deployment asíncrono con Celery**:
   - Instalar Redis o RabbitMQ como message broker
   - Configurar Celery workers
   - Convertir `deploy_vm()` en una tarea Celery
   - Implementar polling AJAX en la página de historial

2. **Agregar barra de progreso**:
   - Usar WebSockets o Server-Sent Events (SSE)
   - Mostrar progreso en tiempo real:
     * ⏳ Creando VM...
     * ⏳ Provisionando...
     * ⏳ Cambiando red...
     * ⏳ Reiniciando...
     * ✅ Completado

3. **Implementar rate limiting**:
   - Limitar número de deployments simultáneos
   - Usar django-ratelimit (ya instalado)

## Referencias

- [mod_wsgi Configuration](https://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGIDaemonProcess.html)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Async Views](https://docs.djangoproject.com/en/5.0/topics/async/)
