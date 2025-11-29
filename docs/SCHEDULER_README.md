# Scheduler - Guía de Uso

## 📋 Descripción

El scheduler ejecuta tareas programadas de Ansible en el momento especificado. Soporta dos modos de operación:

1. **Modo Daemon** (Recomendado) - Corre continuamente monitoreando tareas
2. **Modo Cron** - Se ejecuta periódicamente vía crontab

---

## 🚀 Inicio Rápido

### Opción 1: Modo Daemon (RECOMENDADO)

**Para ver el estado "Running" en tiempo real, usa el modo daemon:**

```bash
# Iniciar daemon en background
nohup /opt/www/app/run_scheduler_daemon.sh >> /var/log/scheduler_daemon.log 2>&1 &

# Ver el log en tiempo real
tail -f /var/log/scheduler_daemon.log

# Detener el daemon
ps aux | grep run_scheduled_tasks
kill <PID>
```

**Ventajas del modo daemon:**
- ✅ Monitoreo continuo cada 10 segundos
- ✅ Estado "Running" visible en la UI (delay de 2 segundos)
- ✅ No pierde tareas
- ✅ Ideal para desarrollo y producción

---

### Opción 2: Modo Cron

**Para ejecución periódica sin daemon:**

```bash
# Editar crontab
crontab -e

# Agregar esta línea (ejecuta cada minuto)
* * * * * /opt/www/app/run_scheduler.sh >> /var/log/scheduler.log 2>&1
```

**Ventajas del modo cron:**
- ✅ No requiere proceso en background
- ✅ Reinicia automáticamente si falla
- ⚠️ Estado "Running" puede no ser visible si la tarea es muy rápida

---

## 🎯 Uso Manual

### Ejecutar una vez (testing)

```bash
cd /opt/www/app
source venv/bin/activate
python manage.py run_scheduled_tasks
```

### Ejecutar en modo daemon manualmente

```bash
cd /opt/www/app
source venv/bin/activate
python manage.py run_scheduled_tasks --daemon --interval 10
```

**Opciones:**
- `--daemon`: Ejecuta en loop continuo
- `--interval N`: Intervalo en segundos entre chequeos (default: 10)

---

## 📊 Monitoreo de Tareas

### Ver tareas programadas

1. Navega a: **Deploy → Scheduled Tasks**
2. La página se auto-actualiza cada 5 segundos
3. Filtra por estado: Pending, Running, Completed, Failed

### Estados de las tareas

| Estado | Color | Descripción |
|--------|-------|-------------|
| **Pending** | 🟡 Amarillo | Esperando hora programada |
| **Running** | 🔵 Azul | Ejecutándose ahora (visible por 2+ segundos) |
| **Completed** | 🟢 Verde | Finalizado exitosamente |
| **Failed** | 🔴 Rojo | Ejecución fallida |
| **Cancelled** | ⚪ Gris | Cancelado manualmente |

---

## 🔍 Troubleshooting

### El scheduler no ejecuta las tareas

```bash
# Verificar si el daemon está corriendo
ps aux | grep run_scheduled_tasks

# Si no está corriendo, iniciarlo
nohup /opt/www/app/run_scheduler_daemon.sh >> /var/log/scheduler_daemon.log 2>&1 &
```

### No veo el estado "Running"

**Solución:** Usa el modo daemon en lugar de cron.

El modo daemon incluye un delay de 2 segundos después de marcar la tarea como "running", lo que permite que la UI (con auto-refresh de 5s) capture ese estado.

### Ver logs del scheduler

```bash
# Modo daemon
tail -f /var/log/scheduler_daemon.log

# Modo cron
tail -f /var/log/scheduler.log
```

### Reiniciar el scheduler

```bash
# Detener
ps aux | grep run_scheduled_tasks
kill <PID>

# Iniciar
nohup /opt/www/app/run_scheduler_daemon.sh >> /var/log/scheduler_daemon.log 2>&1 &
```

---

## 🎬 Flujo Completo

### 1. Programar una tarea

```
Deploy → Execute Playbook
  ↓
✓ Schedule for later execution
  ↓
Seleccionar fecha/hora
  ↓
Execute Playbook
  ↓
Mensaje azul: "Task Scheduled Successfully" + Task ID
```

### 2. Monitorear la ejecución

```
Deploy → Scheduled Tasks
  ↓
Ver tarea en estado "Pending" (amarillo)
  ↓
Cuando llega la hora:
  ↓
Estado cambia a "Running" (azul con spinner) - 2+ segundos
  ↓
Estado cambia a "Completed" (verde) o "Failed" (rojo)
  ↓
Click en la tarea para ver output completo
```

---

## 📝 Notas Importantes

1. **Auto-refresh:** La página de Scheduled Tasks se actualiza cada 5 segundos automáticamente
2. **Delay de 2 segundos:** Después de marcar como "running", hay un delay intencional para que la UI pueda mostrar ese estado
3. **Intervalo del daemon:** Por defecto chequea cada 10 segundos. Puedes cambiarlo con `--interval N`
4. **Timezone:** Las tareas usan el timezone configurado en Django (settings.py)

---

## 🔧 Configuración Avanzada

### Cambiar intervalo del daemon

Edita `/opt/www/app/run_scheduler_daemon.sh`:

```bash
# Cambiar de 10 a 5 segundos
python manage.py run_scheduled_tasks --daemon --interval 5
```

### Ejecutar como servicio systemd

Crea `/etc/systemd/system/diaken-scheduler.service`:

```ini
[Unit]
Description=Diaken Scheduler Daemon
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/www/app
ExecStart=/opt/www/app/run_scheduler_daemon.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Luego:

```bash
sudo systemctl daemon-reload
sudo systemctl enable diaken-scheduler
sudo systemctl start diaken-scheduler
sudo systemctl status diaken-scheduler
```

---

## ✅ Checklist de Producción

- [ ] Scheduler daemon corriendo en background
- [ ] Logs configurados en `/var/log/scheduler_daemon.log`
- [ ] Auto-refresh funcionando en UI (cada 5s)
- [ ] Estados visibles: Pending → Running → Completed
- [ ] Servicio systemd configurado (opcional pero recomendado)
- [ ] Monitoreo de logs configurado

---

**¡El scheduler está listo para usar!** 🎉
