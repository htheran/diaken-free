# Deployment Cleanup System

## Problema identificado

Los deployments pueden quedarse en estado "running" indefinidamente por las siguientes razones:

1. **Proceso bloqueante**: Django usa `subprocess.run()` que es bloqueante. Si el servidor se reinicia mientras un playbook está corriendo, el proceso de Ansible puede seguir ejecutándose pero Django pierde la referencia.

2. **Sin recuperación**: No hay mecanismo para verificar si los deployments "running" realmente tienen un proceso activo después de un reinicio.

3. **Timeout limitado**: El timeout de 10 minutos solo funciona si el servidor Django está corriendo.

## Solución implementada

### 1. Comando de Management: `cleanup_stuck_deployments`

Este comando identifica y marca como "failed" los deployments y scheduled tasks que llevan más de X horas corriendo.

**Uso:**

```bash
# Ver qué se haría sin ejecutar (dry-run)
python manage.py cleanup_stuck_deployments --dry-run

# Ejecutar con timeout de 6 horas (default)
python manage.py cleanup_stuck_deployments

# Ejecutar con timeout personalizado (ej: 1 hora)
python manage.py cleanup_stuck_deployments --timeout-hours 1

# Ejecutar con timeout de 4 horas
python manage.py cleanup_stuck_deployments --timeout-hours 4
```

**Opciones:**
- `--timeout-hours N`: Número de horas después de las cuales un deployment se considera stuck (default: 6)
- `--dry-run`: Muestra qué se haría sin ejecutar realmente

### 2. Script de Cron: `cleanup_stuck_deployments.sh`

Script bash para ejecutar automáticamente la limpieza.

**Instalación en crontab:**

```bash
# Editar crontab
crontab -e

# Agregar esta línea para ejecutar cada 30 minutos
*/30 * * * * /opt/www/app/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1

# O cada hora
0 * * * * /opt/www/app/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1
```

### 3. Mejoras en la Vista de Historial

- **Ordenamiento**: Los deployments ahora se ordenan por fecha descendente (más recientes primero)
- **Indicador visual**: Los deployments que llevan más de 6 horas corriendo se marcan como "Stuck" con badge rojo
- **Información detallada**: Muestra cuántas horas lleva corriendo un deployment

### 4. Indicadores visuales en la UI

En la lista de historial (`/history/`):
- ✅ **Success**: Badge verde
- ❌ **Failed**: Badge rojo
- ⚠️ **Running**: Badge amarillo (< 6 horas)
- 🚨 **Stuck**: Badge rojo con tiempo (> 6 horas)

## Ejecución manual

Si encuentras deployments stuck, puedes limpiarlos manualmente:

```bash
cd /opt/www/app
source venv/bin/activate

# Ver qué deployments están stuck
python manage.py cleanup_stuck_deployments --dry-run

# Limpiar deployments stuck
python manage.py cleanup_stuck_deployments
```

## Logs

Los logs del cron job se guardan en:
```
/var/log/cleanup_stuck_deployments.log
```

Para ver los logs:
```bash
tail -f /var/log/cleanup_stuck_deployments.log
```

## Recomendaciones

1. **Ejecutar el cleanup regularmente**: Configura el cron job para ejecutarse cada 30 minutos o cada hora.

2. **Ajustar el timeout**: Si tus playbooks normalmente tardan más de 6 horas, ajusta el `--timeout-hours` en el script.

3. **Monitorear logs**: Revisa regularmente los logs para identificar patrones de deployments stuck.

4. **Investigar causas**: Si ves muchos deployments stuck, investiga por qué:
   - ¿Los hosts están inaccesibles?
   - ¿Los playbooks tienen tareas que se cuelgan?
   - ¿Hay problemas de red?

## Solución a largo plazo

Para una solución más robusta, considera:

1. **Usar Celery**: Ejecutar playbooks en background workers con mejor gestión de procesos
2. **Guardar PIDs**: Almacenar el PID del proceso de Ansible para poder verificar si sigue corriendo
3. **Heartbeat**: Implementar un sistema de heartbeat que actualice el deployment cada X segundos
4. **Timeout en Ansible**: Configurar timeouts a nivel de Ansible playbook

## Archivos creados

- `/opt/www/app/history/management/commands/cleanup_stuck_deployments.py` - Comando de management
- `/opt/www/app/cleanup_stuck_deployments.sh` - Script de cron
- `/opt/www/app/DEPLOYMENT_CLEANUP_README.md` - Esta documentación
- Modificaciones en `/opt/www/app/history/views.py` - Ordenamiento y detección de stuck
- Modificaciones en `/opt/www/app/templates/history/history_list.html` - Indicadores visuales

## Testing

Para probar el sistema:

1. Ejecuta el comando en modo dry-run:
   ```bash
   python manage.py cleanup_stuck_deployments --dry-run
   ```

2. Verifica que identifica correctamente los deployments stuck

3. Ejecuta sin dry-run para limpiar:
   ```bash
   python manage.py cleanup_stuck_deployments
   ```

4. Verifica en la UI que los deployments ahora muestran status "Failed"

5. Revisa que el mensaje de timeout aparece en el ansible_output
