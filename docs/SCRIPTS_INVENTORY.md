# 📋 Inventory of Scripts and Tools

## ✅ Scripts Útiles y Activos

### **1. cleanup_stuck_deployments.sh** ⭐
**Ubicación**: `/opt/www/app/cleanup_stuck_deployments.sh`  
**Propósito**: Limpia deployments y tareas que llevan más de 2 horas corriendo  
**Uso**: Automático vía cron (cada 30 minutos)  
**Estado**: ✅ **ACTIVO Y ÚTIL**

**Cron configurado**:
```bash
*/30 * * * * /opt/www/app/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1
```

**Gestión desde GUI**: 
- URL: http://localhost:8001/history/cleanup/
- Permite ejecutar manualmente con diferentes timeouts
- Modo dry-run para previsualizar
- Ver deployments actualmente corriendo

---

### **2. run_scheduler.sh** ⭐
**Ubicación**: `/opt/www/app/run_scheduler.sh`  
**Propósito**: Ejecuta tareas programadas (scheduled tasks)  
**Uso**: Debe ejecutarse cada minuto vía cron  
**Estado**: ✅ **ACTIVO Y NECESARIO**

**Contenido**:
```bash
#!/bin/bash
cd /opt/www/app
source venv/bin/activate
python manage.py run_scheduled_tasks
```

**Cron recomendado**:
```bash
* * * * * /opt/www/app/run_scheduler.sh >> /var/log/scheduler.log 2>&1
```

**Nota**: Este script es **ESENCIAL** para que funcionen las tareas programadas.

---

### **3. run_scheduler_daemon.sh** ⚠️
**Ubicación**: `/opt/www/app/run_scheduler_daemon.sh`  
**Propósito**: Ejecuta el scheduler en modo daemon (continuamente)  
**Uso**: Alternativa a run_scheduler.sh  
**Estado**: ⚠️ **OPCIONAL** (usa uno u otro, no ambos)

**Contenido**:
```bash
#!/bin/bash
cd /opt/www/app
source venv/bin/activate
python manage.py run_scheduled_tasks --daemon --interval 10
```

**Uso**:
```bash
nohup /opt/www/app/run_scheduler_daemon.sh >> /var/log/scheduler_daemon.log 2>&1 &
```

**Recomendación**: 
- Usa `run_scheduler.sh` con cron (más simple y confiable)
- O usa `run_scheduler_daemon.sh` como servicio systemd
- **NO uses ambos al mismo tiempo**

---

## 🛠️ Management Commands

### **1. cleanup_stuck_deployments** ⭐
**Comando**: `python manage.py cleanup_stuck_deployments`  
**Propósito**: Limpia deployments stuck  
**Estado**: ✅ **ACTIVO Y ÚTIL**

**Opciones**:
```bash
# Dry run (solo ver qué se haría)
python manage.py cleanup_stuck_deployments --dry-run

# Ejecutar con timeout de 2 horas (default)
python manage.py cleanup_stuck_deployments

# Timeout personalizado
python manage.py cleanup_stuck_deployments --timeout-hours 4
```

**GUI**: Disponible en http://localhost:8001/history/cleanup/

---

### **2. run_scheduled_tasks** ⭐
**Comando**: `python manage.py run_scheduled_tasks`  
**Propósito**: Ejecuta tareas programadas pendientes  
**Estado**: ✅ **ACTIVO Y NECESARIO**

**Opciones**:
```bash
# Ejecutar una vez
python manage.py run_scheduled_tasks

# Modo daemon (ejecutar continuamente)
python manage.py run_scheduled_tasks --daemon --interval 10
```

---

## 📊 Resumen de Configuración Recomendada

### **Crontab Completo**:

```bash
# Editar crontab
crontab -e

# Agregar estas líneas:

# 1. Ejecutar tareas programadas cada minuto
* * * * * /opt/www/app/run_scheduler.sh >> /var/log/scheduler.log 2>&1

# 2. Limpiar deployments stuck cada 30 minutos
*/30 * * * * /opt/www/app/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1
```

### **Verificar crontab actual**:
```bash
crontab -l
```

### **Ver logs**:
```bash
# Scheduler
tail -f /var/log/scheduler.log

# Cleanup
tail -f /var/log/cleanup_stuck_deployments.log
```

---

## 🎯 Gestión desde la GUI

### **1. Cleanup de Deployments Stuck**
**URL**: http://localhost:8001/history/cleanup/

**Funcionalidades**:
- ✅ Ejecutar cleanup manualmente
- ✅ Configurar timeout personalizado
- ✅ Modo dry-run para previsualizar
- ✅ Ver deployments actualmente corriendo
- ✅ Ver resultados en tiempo real
- ✅ Información de ayuda integrada

**Ventajas**:
- No necesitas acceso SSH/consola
- Interfaz visual clara
- Previsualización antes de ejecutar
- Historial de acciones

---

## ⚠️ Respuestas a tus Preguntas

### **1. ¿Qué pasa si una tarea va bien pero demora más del tiempo esperado?**

**Problema**: Con el timeout de 2 horas, se marcaría como "failed" incluso si está funcionando correctamente.

**Soluciones**:

#### **Opción A: Ajustar el timeout global** (Fácil)
Edita `cleanup_stuck_deployments.sh`:
```bash
python manage.py cleanup_stuck_deployments --timeout-hours 4  # 4 horas en lugar de 2
```

#### **Opción B: Usar la GUI con timeout personalizado** (Recomendado)
1. Ve a http://localhost:8001/history/cleanup/
2. Cambia el timeout a 4, 6, u 8 horas según necesites
3. Ejecuta manualmente cuando sea necesario

#### **Opción C: Deshabilitar el cron y usar solo GUI** (Más control)
```bash
# Comentar la línea en crontab
crontab -e
# Agregar # al inicio:
# */30 * * * * /opt/www/app/cleanup_stuck_deployments.sh >> /var/log/cleanup_stuck_deployments.log 2>&1
```

Luego ejecuta manualmente desde la GUI cuando lo necesites.

---

### **2. ¿Las tareas programadas a 5 días se interrumpen?**

**Respuesta**: **NO**

El script solo afecta deployments con status="running", no los que están:
- ✅ "pending" (esperando ser ejecutados)
- ✅ "scheduled" (programados para el futuro)
- ✅ "success" (ya completados)
- ✅ "failed" (ya fallidos)

Solo afecta deployments que **están corriendo actualmente** por más de X horas.

---

### **3. ¿Cómo tener control desde la GUI?**

**Respuesta**: ✅ **Ya está implementado**

**URL**: http://localhost:8001/history/cleanup/

**Funcionalidades**:
1. **Ver deployments corriendo**: Lista en tiempo real
2. **Ejecutar cleanup manual**: Con timeout personalizado
3. **Dry run**: Previsualizar sin ejecutar
4. **Resultados detallados**: Ver qué se limpió
5. **Ayuda integrada**: Documentación en la misma página

**Acceso**:
- Desde el menú: History → Botón "Cleanup Stuck Deployments"
- URL directa: http://localhost:8001/history/cleanup/

---

## 🔧 Recomendaciones Finales

### **Para Producción**:

1. **Usa la GUI para cleanup manual**:
   - Más control
   - Previsualización
   - Timeout personalizado por caso

2. **Ajusta el timeout del cron según tus necesidades**:
   - Si tus playbooks tardan 1-2 horas: timeout de 3-4 horas
   - Si tus playbooks tardan 3-4 horas: timeout de 6-8 horas

3. **Monitorea los logs regularmente**:
   ```bash
   tail -f /var/log/cleanup_stuck_deployments.log
   ```

4. **Considera deshabilitar el cron automático**:
   - Usa solo la GUI para mayor control
   - Ejecuta manualmente cuando sea necesario

### **Configuración Conservadora** (Recomendada para producción):

```bash
# Editar cleanup_stuck_deployments.sh
python manage.py cleanup_stuck_deployments --timeout-hours 6  # 6 horas

# O deshabilitar el cron y usar solo GUI
```

---

## 📝 Checklist de Configuración

- [x] ✅ Cron de cleanup configurado (cada 30 min)
- [ ] ⚠️ Cron de scheduler configurado (cada minuto) - **PENDIENTE**
- [x] ✅ GUI de cleanup disponible
- [x] ✅ Scripts con permisos de ejecución
- [ ] ⚠️ Logs configurados y monitoreados

### **Acción Pendiente**:

```bash
# Agregar scheduler a crontab
crontab -e

# Agregar esta línea:
* * * * * /opt/www/app/run_scheduler.sh >> /var/log/scheduler.log 2>&1
```

---

## 🎓 Documentación Adicional

- **DEPLOYMENT_CLEANUP_README.md**: Guía técnica detallada
- **STUCK_DEPLOYMENTS_SOLUTION.md**: Explicación del problema y solución
- **SCRIPTS_INVENTORY.md**: Este documento

---

## 📞 Soporte

Si tienes dudas:
1. Revisa la GUI: http://localhost:8001/history/cleanup/
2. Consulta los logs: `/var/log/cleanup_stuck_deployments.log`
3. Ejecuta en dry-run primero: `python manage.py cleanup_stuck_deployments --dry-run`
