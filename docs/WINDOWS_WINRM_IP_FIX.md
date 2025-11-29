# Solución al Problema de WinRM con Cambios de IP en Windows

## 🔍 Problema Identificado

**Síntoma:**
- ✅ El aprovisionamiento de VMs Windows funciona correctamente (cambia IP, hostname, reinicia)
- ❌ Después del despliegue, NO se pueden ejecutar playbooks en el host Windows
- ❌ Error: `Connection reset by peer` o `UNREACHABLE`

**Causa Raíz:**
El listener de WinRM estaba configurado para una **IP específica** (la IP de la plantilla), en lugar de escuchar en **todas las IPs** (Address=*).

Cuando se clona una VM y se le cambia la IP:
1. VM arranca con IP de plantilla (ej: 10.100.18.80) ✅
2. Ansible conecta via WinRM a IP de plantilla ✅
3. Playbook cambia IP a nueva (ej: 10.100.5.89) ✅
4. VM reinicia con nueva IP ✅
5. **WinRM NO escucha en la nueva IP** ❌ → Conexión falla

---

## ✅ Solución Implementada

### 1. **Script de Preparación de Plantilla** (NUEVO)

He creado un script mejorado para preparar la plantilla de Windows:

📄 **Archivo:** `/opt/www/app/scripts/windows_template_setup.ps1`

**Características clave:**
```powershell
# ⭐ LO MÁS IMPORTANTE: Listener para TODAS las IPs
winrm create winrm/config/Listener?Address=*+Transport=HTTP

# En lugar de:
# winrm create winrm/config/Listener?Address=10.100.18.80+Transport=HTTP ❌
```

**Cómo usar:**
1. Conectarse a la plantilla de Windows via RDP o consola
2. Abrir PowerShell como Administrador
3. Ejecutar el script:
   ```powershell
   # Copiar el contenido del script o ejecutarlo desde compartido
   .\windows_template_setup.ps1
   ```
4. Verificar que muestra: ✓ Listener created for Address=* (all IPs)
5. Apagar la VM y convertirla en plantilla

---

### 2. **Reconfiguración Automática en Aprovisionamiento** (NUEVO)

He agregado una tarea **CRÍTICA** al playbook de aprovisionamiento que reconfigura WinRM **DESPUÉS** del cambio de IP pero **ANTES** del reinicio:

📄 **Archivo:** `/opt/www/app/ansible/provision_windows_vm.yml`

**Nueva tarea agregada:**
```yaml
- name: Reconfigure WinRM for new IP address (CRITICAL)
  win_shell: |
    # Remove old listeners (tied to old IP)
    Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force
    
    # Create new listener for ALL IPs (Address=*)
    winrm create winrm/config/Listener?Address=*+Transport=HTTP
    
    # Configure TrustedHosts, auth methods, etc.
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
    Set-Service WinRM -StartupType Automatic
    Restart-Service WinRM
```

**Orden de ejecución:**
1. Programar reinicio en 40 segundos
2. Cambiar hostname
3. Cambiar IP
4. **⭐ Reconfigurar WinRM para nueva IP** ← NUEVO
5. Reiniciar
6. **WinRM funciona con nueva IP** ✅

---

## 🎯 Beneficios

### Antes:
```
Plantilla IP: 10.100.18.80
  ↓ WinRM Listener: Address=10.100.18.80 ❌
  ↓ Clonar VM
  ↓ Cambiar IP a: 10.100.5.89
  ↓ Reiniciar
  ↓ WinRM NO escucha en 10.100.5.89 ❌
  ↓ Playbooks fallan ❌
```

### Ahora:
```
Plantilla IP: 10.100.18.80
  ↓ WinRM Listener: Address=* (todas las IPs) ✅
  ↓ Clonar VM
  ↓ Cambiar IP a: 10.100.5.89
  ↓ Reconfigurar WinRM (Address=*) ✅
  ↓ Reiniciar
  ↓ WinRM escucha en 10.100.5.89 ✅
  ↓ Playbooks funcionan ✅
```

---

## 🔧 Pasos para Implementar

### Opción A: Recrear Plantilla (Recomendado)

1. **Crear nueva VM Windows desde cero**

2. **Ejecutar script de configuración:**
   ```powershell
   # En la VM, PowerShell como Administrador:
   # Copiar contenido de: /opt/www/app/scripts/windows_template_setup.ps1
   # Y ejecutarlo
   ```

3. **Verificar configuración:**
   ```powershell
   winrm enumerate winrm/config/listener
   ```
   
   Debe mostrar:
   ```
   Listener
       Address = *
       Transport = HTTP
       Port = 5985
   ```

4. **Apagar y convertir en plantilla**

5. **Probar clonado de VM:**
   - Desplegar nueva VM usando la nueva plantilla
   - Verificar que el aprovisionamiento funciona
   - Verificar que después puedes ejecutar playbooks de actualización

---

### Opción B: Corregir VMs Ya Desplegadas

Si ya tienes VMs desplegadas con el problema, conéctate a cada una via RDP:

```powershell
# En cada VM Windows, PowerShell como Administrador:

# 1. Eliminar listeners antiguos
Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force

# 2. Crear listener para todas las IPs
winrm create winrm/config/Listener?Address=*+Transport=HTTP

# 3. Configurar TrustedHosts
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# 4. Habilitar autenticación
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# 5. Reiniciar WinRM
Restart-Service WinRM

# 6. Verificar
Test-WSMan -ComputerName localhost
```

Después de esto, los playbooks deberían funcionar.

---

## 🧪 Pruebas

### Probar WinRM desde el servidor Ansible:

```bash
cd /opt/www/app
source venv/bin/activate

# Crear inventory de prueba
cat > /tmp/test_win.ini << 'EOF'
[windows_hosts]
10.100.5.89

[windows_hosts:vars]
ansible_user=Administrator
ansible_password=tu_password
ansible_connection=winrm
ansible_winrm_transport=ntlm
ansible_port=5985
ansible_winrm_server_cert_validation=ignore
EOF

# Probar ping
ansible windows_hosts -i /tmp/test_win.ini -m win_ping
```

**Resultado esperado:**
```json
10.100.5.89 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

---

## 📊 Checklist de Verificación

**En la Plantilla de Windows:**
- [ ] WinRM listener configurado con `Address=*`
- [ ] TrustedHosts configurado con `*`
- [ ] Firewall permite puerto 5985
- [ ] WinRM service en modo Automatic startup
- [ ] Test local: `Test-WSMan -ComputerName localhost` funciona

**En el Playbook de Aprovisionamiento:**
- [ ] Tarea de reconfiguración de WinRM agregada
- [ ] Se ejecuta DESPUÉS del cambio de IP
- [ ] Se ejecuta ANTES del reinicio

**En VMs Desplegadas:**
- [ ] Aprovisionamiento exitoso (IP, hostname cambiados)
- [ ] Después del reinicio, ping funciona
- [ ] WinRM responde en nueva IP
- [ ] Playbooks de actualización funcionan

---

## 🎓 Conceptos Clave

### ¿Qué significa `Address=*`?

```powershell
# ❌ MAL - Escucha solo en una IP específica:
Address=10.100.18.80

# ✅ BIEN - Escucha en TODAS las interfaces:
Address=*
```

Esto significa que WinRM escuchará en:
- 127.0.0.1 (localhost)
- 10.100.18.80 (IP de plantilla)
- 10.100.5.89 (IP después del cambio)
- Cualquier otra IP que se configure

### ¿Por qué funciona el aprovisionamiento inicial?

Porque cuando se clona la VM, inicialmente tiene la **IP de la plantilla**.
El playbook conecta a esa IP, que **sí tiene** el listener de WinRM funcionando.

El problema aparece **DESPUÉS del reinicio**, cuando la VM ya tiene la nueva IP.

---

## 📝 Archivos Modificados

1. **Nuevo script de plantilla:**
   ```
   /opt/www/app/scripts/windows_template_setup.ps1
   ```

2. **Playbook de aprovisionamiento actualizado:**
   ```
   /opt/www/app/ansible/provision_windows_vm.yml
   ```
   - Agregada tarea: "Reconfigure WinRM for new IP address (CRITICAL)"

3. **Scheduler con soporte Windows:**
   ```
   /opt/www/app/scheduler/management/commands/run_scheduled_tasks.py
   ```
   - Detecta OS del host
   - Usa WinRM para Windows, SSH para Linux

---

## ✅ Resumen

**Problema:** Listener de WinRM atado a IP de plantilla
**Solución:** Configurar listener con `Address=*` (todas las IPs)
**Implementación:**
  1. Script de plantilla mejorado
  2. Reconfiguración automática en aprovisionamiento
  3. Scheduler actualizado con soporte Windows

**Estado:** 
- ✅ Plantilla preparada correctamente = VMs funcionan después del despliegue
- ✅ Aprovisionamiento reconfigura WinRM = Playbooks funcionan siempre
- ✅ Scheduler detecta Windows = Tareas programadas funcionan

---

## 🆘 Troubleshooting

**Si el aprovisionamiento falla:**
```powershell
# En la VM Windows, verificar listener:
winrm enumerate winrm/config/listener

# Debe mostrar Address = *
```

**Si los playbooks fallan después del despliegue:**
```bash
# Desde el servidor Ansible:
ansible windows_hosts -i inventory.ini -m win_ping -vvv

# Revisar logs de WinRM en Windows:
Get-EventLog -LogName "Microsoft-Windows-WinRM/Operational" -Newest 20
```

**Si nada funciona:**
1. RDP a la VM
2. Ejecutar script de corrección (Opción B)
3. Probar `Test-WSMan -ComputerName localhost`
4. Probar desde Ansible

---

**¡La configuración de WinRM ahora es dinámica y sobrevive cambios de IP!** 🎉
