# Scripts de Utilidad para Windows

Esta carpeta contiene scripts de PowerShell y Bash para configuración y diagnóstico de Windows VMs.

---

## 📋 Scripts Disponibles

### 1. `windows_template_setup.ps1`

**Propósito:** Preparar plantilla de Windows para clonado y automatización

**Cuándo usar:** 
- Al crear una nueva plantilla de Windows desde cero
- Al actualizar una plantilla existente con problemas de WinRM

**Qué hace:**
- ✅ Configura WinRM para escuchar en **todas las IPs** (Address=*)
- ✅ Habilita PowerShell Remoting
- ✅ Configura TrustedHosts para aceptar conexiones
- ✅ Habilita autenticación Basic, Negotiate y CredSSP
- ✅ Configura firewall para puertos 5985 y 5986
- ✅ Establece servicio WinRM en modo Automatic
- ✅ Verifica la configuración

**Cómo usar:**
1. Conectarse a la VM Windows (RDP o consola)
2. Abrir PowerShell como Administrador
3. Copiar el contenido del script o ejecutarlo:
   ```powershell
   # Si tienes el archivo:
   Set-ExecutionPolicy Bypass -Scope Process -Force
   .\windows_template_setup.ps1
   
   # O copiar/pegar el contenido completo
   ```
4. Verificar que todos los pasos muestran ✓
5. Apagar la VM
6. Convertir en plantilla en vCenter

**Salida esperada:**
```
✓ PowerShell Remoting enabled
✓ WinRM service configured for automatic startup
✓ Existing listeners removed
✓ WinRM listener created for Address=* (all IPs)
✓ TrustedHosts configured to accept all connections
...
✓ WinRM local connection test PASSED
```

---

### 2. `winrm_post_provision_fix.ps1`

**Propósito:** Corregir WinRM en VMs ya desplegadas que tienen problemas de conectividad

**Cuándo usar:**
- Cuando una VM Windows desplegada no acepta conexiones WinRM
- Después de un cambio de IP que rompió la conectividad
- Para VMs creadas con plantilla antigua (sin Address=*)

**Qué hace:**
- ✅ Elimina listeners antiguos (atados a IP específica)
- ✅ Crea nuevo listener para todas las IPs (Address=*)
- ✅ Reconfigura TrustedHosts
- ✅ Reinicia servicio WinRM

**Cómo usar:**
1. Conectarse a la VM Windows con problemas (RDP o consola)
2. Abrir PowerShell como Administrador
3. Ejecutar:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   .\winrm_post_provision_fix.ps1
   ```
4. Probar conectividad desde servidor Ansible

**Salida esperada:**
```
Reconfiguring WinRM for new IP address...
WinRM reconfigured successfully
```

---

### 3. `test_windows_winrm.sh`

**Propósito:** Probar conectividad WinRM desde el servidor Ansible/Linux

**Cuándo usar:**
- Después de configurar una nueva plantilla
- Después de desplegar una nueva VM
- Para diagnosticar problemas de conectividad
- Antes de ejecutar playbooks en producción

**Qué hace:**
- ✅ Prueba conectividad de red (ping)
- ✅ Prueba puerto WinRM (5985/5986)
- ✅ Prueba autenticación WinRM (win_ping)
- ✅ Obtiene información del sistema Windows

**Cómo usar:**
```bash
cd /opt/www/app
source venv/bin/activate

# Sintaxis básica
./scripts/test_windows_winrm.sh <IP> <Usuario> <Contraseña>

# Ejemplo con NTLM (por defecto)
./scripts/test_windows_winrm.sh 10.100.5.89 Administrator MyPass123

# Ejemplo con Basic auth y puerto custom
./scripts/test_windows_winrm.sh 10.100.5.89 Administrator MyPass123 basic 5986
```

**Salida esperada (éxito):**
```
=======================================
WinRM Connection Test
=======================================

[1/4] Testing network connectivity...
✓ Network ping successful

[2/4] Testing WinRM port connectivity...
✓ Port 5985 is open

[3/4] Testing WinRM authentication (win_ping)...
✓ WinRM authentication successful
✓ win_ping module returned 'pong'

[4/4] Gathering Windows system information...
hostname: MYSERVER
IPv4 Address: 10.100.5.89

=======================================
✓ WinRM Connection Test PASSED
=======================================
```

**Salida de error (conectividad):**
```
[2/4] Testing WinRM port connectivity...
✗ Port 5985 is closed or unreachable
Make sure WinRM is enabled and firewall allows port 5985
```

**Salida de error (autenticación):**
```
[3/4] Testing WinRM authentication (win_ping)...
✗ WinRM authentication failed

Running detailed test...
fatal: [10.100.5.89]: UNREACHABLE! => {
  "msg": "ntlm: ('Connection aborted.', ...)"
}
```

---

## 🔧 Flujo de Trabajo Completo

### Escenario 1: Nueva Plantilla de Windows

```bash
# 1. En la VM Windows (PowerShell como Admin):
.\windows_template_setup.ps1

# 2. Verificar en Windows:
winrm enumerate winrm/config/listener
# Debe mostrar: Address = *

# 3. Apagar y convertir en plantilla

# 4. Después de crear VM desde plantilla, probar desde Linux:
./scripts/test_windows_winrm.sh 10.100.5.89 Administrator Pass123

# 5. Si el test pasa, la VM está lista para automatización
```

### Escenario 2: Corregir VM Existente

```bash
# 1. En la VM Windows con problemas (PowerShell como Admin):
.\winrm_post_provision_fix.ps1

# 2. Probar desde servidor Linux:
./scripts/test_windows_winrm.sh 10.100.5.89 Administrator Pass123

# 3. Si el test pasa, ejecutar playbooks normalmente
```

---

## 📊 Verificación Manual

### En Windows (PowerShell como Administrator):

```powershell
# Ver listeners de WinRM
winrm enumerate winrm/config/listener

# Debe mostrar:
#   Listener
#       Address = *          ← IMPORTANTE: debe ser asterisco, no IP
#       Transport = HTTP
#       Port = 5985

# Ver configuración completa
winrm get winrm/config

# Probar conexión local
Test-WSMan -ComputerName localhost

# Ver estado del servicio
Get-Service WinRM

# Ver logs recientes
Get-EventLog -LogName "Microsoft-Windows-WinRM/Operational" -Newest 20
```

### En Linux (Ansible):

```bash
# Activar entorno virtual
cd /opt/www/app
source venv/bin/activate

# Crear inventory temporal
cat > /tmp/test.ini << 'EOF'
[windows_hosts]
10.100.5.89

[windows_hosts:vars]
ansible_user=Administrator
ansible_password=YourPassword
ansible_connection=winrm
ansible_winrm_transport=ntlm
ansible_port=5985
ansible_winrm_server_cert_validation=ignore
EOF

# Probar ping
ansible windows_hosts -i /tmp/test.ini -m win_ping

# Probar comando
ansible windows_hosts -i /tmp/test.ini -m win_shell -a "hostname"

# Cleanup
rm /tmp/test.ini
```

---

## ❗ Problemas Comunes

### Problema: "Port 5985 is closed or unreachable"

**Causa:** Firewall bloqueando WinRM o servicio detenido

**Solución en Windows:**
```powershell
# Verificar servicio
Get-Service WinRM
Start-Service WinRM

# Agregar regla de firewall
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985
```

---

### Problema: "Connection aborted" o "Connection reset by peer"

**Causa:** Listener atado a IP específica en lugar de Address=*

**Solución en Windows:**
```powershell
# Ejecutar el script de corrección
.\winrm_post_provision_fix.ps1

# O manualmente:
Get-ChildItem WSMan:\localhost\Listener | Remove-Item -Recurse -Force
winrm create winrm/config/Listener?Address=*+Transport=HTTP
Restart-Service WinRM
```

---

### Problema: "Access denied" o "Authentication failed"

**Causa:** Credenciales incorrectas o tipo de autenticación no habilitado

**Solución en Windows:**
```powershell
# Habilitar autenticación Basic y Negotiate
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
Restart-Service WinRM
```

**Solución en Linux:**
```bash
# Probar con tipo de autenticación diferente
./scripts/test_windows_winrm.sh 10.100.5.89 Administrator Pass123 basic
```

---

## 🎯 Checklist de Configuración Correcta

**En la plantilla Windows:**
- [ ] Servicio WinRM: Running y Automatic
- [ ] Listener configurado: Address = * (no IP específica)
- [ ] TrustedHosts: * (acepta todas las fuentes)
- [ ] Autenticación: Basic, Negotiate habilitados
- [ ] Firewall: Puertos 5985 y 5986 permitidos
- [ ] Test local: `Test-WSMan localhost` funciona

**Después del despliegue:**
- [ ] VM tiene IP correcta (verificar con `ipconfig`)
- [ ] Ping desde servidor Ansible funciona
- [ ] Puerto 5985 accesible desde servidor Ansible
- [ ] `test_windows_winrm.sh` pasa todas las pruebas
- [ ] Playbooks Ansible funcionan correctamente

---

## 📚 Documentación Relacionada

- `/opt/www/app/WINDOWS_WINRM_IP_FIX.md` - Análisis completo del problema de IP
- `/opt/www/app/WINRM_SETUP_INSTRUCTIONS.md` - Instrucciones generales de WinRM
- `/opt/www/app/WINRM_POST_DEPLOYMENT_ISSUE.md` - Problemas post-despliegue

---

## 🆘 Soporte

Si los problemas persisten después de seguir todos los pasos:

1. Verificar logs de WinRM en Windows
2. Ejecutar test con modo verbose: `ansible ... -vvv`
3. Verificar que no haya políticas de grupo bloqueando WinRM
4. Verificar que no haya antivirus/EDR bloqueando conexiones
5. Consultar documentación en `/opt/www/app/WINDOWS_WINRM_IP_FIX.md`

---

**¡Scripts listos para automatizar y diagnosticar Windows!** 🎉
