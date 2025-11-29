# Recomendaciones para Actualización de Grupos Windows Heterogéneos

## Grupo: LICENSES-SERVERS (20 servidores)
**Versiones**: Windows Server 2012, 2016, 2019, 2022, 2025

## ✅ Ajustes Aplicados al Playbook

### 1. Estrategia de Ejecución
```yaml
strategy: free
```
- Cada servidor avanza a su propio ritmo
- Los servidores más rápidos no esperan a los lentos
- Reduce el tiempo total de ejecución

### 2. Procesamiento en Lotes
```yaml
serial: 5
```
- Procesa 5 servidores simultáneamente
- Reduce carga en la red y vCenter
- Permite monitoreo más controlado

### 3. Manejo de Errores
```yaml
ignore_unreachable: yes
any_errors_fatal: no
```
- Continúa con otros servidores si algunos no responden
- Un servidor con problemas no detiene todo el grupo
- Genera reporte completo al final

### 4. Timeouts Ajustados

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **WinRM Read Timeout** | 300 seg (5 min) | Tiempo máximo para leer respuesta |
| **WinRM Operation Timeout** | 240 seg (4 min) | Tiempo máximo por operación |
| **Reboot Timeout** | 900 seg (15 min) | Tiempo para reinicio (2012 es más lento) |
| **Update Timeout** | 7200 seg (2 horas) | Tiempo para instalar actualizaciones |
| **Async Timeout** | 3600 seg (1 hora) | Operaciones asíncronas |

### 5. Ciclos de Actualización
```yaml
max_update_cycles: 3
```
- Reducido de 5 a 3 para grupos grandes
- Cada ciclo puede tardar 30-60 minutos
- Total estimado: 1.5 - 3 horas por servidor

## 🔍 Consideraciones por Versión de Windows

### Windows Server 2012 / 2012 R2
- ⚠️ **PowerShell**: Versión 4.0/5.0 (limitado)
- ⚠️ **Reinicio**: Más lento (puede tardar 10-15 minutos)
- ⚠️ **WinRM**: Puede requerir configuración manual
- ⚠️ **Actualizaciones**: Más grandes y numerosas
- 💡 **Recomendación**: Ejecutar en lote separado si es posible

### Windows Server 2016
- ✅ **PowerShell**: 5.1 (completo)
- ✅ **Reinicio**: Normal (5-8 minutos)
- ✅ **WinRM**: Generalmente configurado por defecto
- 💡 **Recomendación**: Buen balance de compatibilidad

### Windows Server 2019 / 2022 / 2025
- ✅ **PowerShell**: 5.1+ (óptimo)
- ✅ **Reinicio**: Rápido (3-5 minutos)
- ✅ **WinRM**: Configurado por defecto
- ✅ **Actualizaciones**: Más eficientes
- 💡 **Recomendación**: Procesamiento más rápido

## 📊 Expectativas de Tiempo

### Por Servidor (promedio)
- **2012**: 2-3 horas
- **2016**: 1.5-2 horas
- **2019+**: 1-1.5 horas

### Grupo Completo (20 servidores)
- **Serial 5**: 8-12 horas total
- **Procesamiento**: 4 lotes de 5 servidores
- **Horario recomendado**: Ventana de mantenimiento nocturna

## 🛠️ Preparación Pre-Ejecución

### 1. Verificar Conectividad WinRM
```powershell
# En cada servidor
Get-Service WinRM
Test-WSMan -ComputerName localhost
```

### 2. Verificar Espacio en Disco
- **Mínimo recomendado**: 10 GB libres en C:\
- **Óptimo**: 20 GB libres

### 3. Verificar Credenciales
- Todas las credenciales deben estar actualizadas
- Probar conexión WinRM antes de ejecutar

### 4. Snapshots (Recomendado)
- ✅ Habilitar checkbox de snapshot
- Se crea un snapshot por servidor antes de actualizar
- Auto-delete configurado (24 horas por defecto)

## 🚨 Hosts Problemáticos Identificados

### Inalcanzables (11 hosts)
```
10.100.9.16, 10.100.9.17, 10.100.9.20, 10.100.9.21, 10.100.9.25
10.100.9.34, 10.100.9.35, 10.100.9.49, 10.100.9.53, 10.100.9.58
10.100.9.66
```

**Acciones requeridas**:
1. Verificar que WinRM esté habilitado
2. Verificar firewall (puerto 5985)
3. Verificar credenciales
4. Probar conexión manual: `Test-WSMan -ComputerName <IP>`

### Con Timeouts Previos (5 hosts)
```
10.100.9.11, 10.100.9.12, 10.100.9.14, 10.100.9.23, 10.100.9.28
```

**Esperado**: Con los nuevos timeouts (300 seg), deberían completar exitosamente

## 📋 Checklist Pre-Ejecución

- [ ] Ventana de mantenimiento aprobada (8-12 horas)
- [ ] Snapshots habilitados en la interfaz
- [ ] Verificar espacio en disco en todos los servidores
- [ ] Probar WinRM en hosts problemáticos
- [ ] Notificar a usuarios de posibles reinicios
- [ ] Tener plan de rollback (restaurar snapshots si es necesario)

## 📈 Monitoreo Durante Ejecución

### En la Interfaz Web
- Ver progreso en tiempo real
- Identificar hosts con problemas
- Ver logs de cada servidor

### Logs a Revisar
- `/var/log/celery/diaken-worker.log`: Logs de ejecución
- Ansible output en la interfaz web
- Reportes BEFORE/AFTER en cada servidor

## 🔄 Post-Ejecución

### 1. Verificar Resultados
- Revisar PLAY RECAP
- Identificar hosts exitosos vs fallidos
- Revisar reportes de auditoría

### 2. Hosts Fallidos
- Revisar logs específicos
- Intentar ejecución individual
- Considerar actualización manual si persiste

### 3. Limpieza
- Snapshots se auto-eliminan después de 24 horas
- Revisar espacio en disco en servidores
- Documentar resultados

## 💡 Mejoras Futuras Sugeridas

1. **Dividir por Versión**: Crear subgrupos por versión de Windows
2. **Horarios Escalonados**: Ejecutar 2012 en horario separado
3. **Pre-checks**: Script de verificación antes de ejecutar
4. **Notificaciones**: Alertas cuando termine cada lote
5. **Dashboard**: Panel de monitoreo en tiempo real

## 📞 Soporte

Si encuentras problemas:
1. Revisar logs en `/var/log/celery/diaken-worker.log`
2. Verificar ansible output en la interfaz
3. Probar conexión WinRM manualmente
4. Contactar al equipo de infraestructura
