# 🔧 Troubleshooting SSH en Deployments

Este documento te ayudará a resolver problemas de conexión SSH durante el despliegue de VMs.

---

## 🚨 Error Común

```
ERROR: SSH not ready on 10.100.18.79 after 120s. VM may not have booted properly.
```

---

## 📋 Checklist de Diagnóstico

### ✅ 1. Verificar que la VM se creó correctamente

```bash
# Verificar en vCenter que la VM existe y está encendida
# O usar govc:
govc vm.info VM_NAME
```

**Síntomas si falla:**
- La VM no aparece en vCenter
- La VM está apagada
- La VM está en estado de error

---

### ✅ 2. Verificar que la llave SSH existe

```bash
# Ver las credenciales configuradas
ls -la /opt/base/app/diaken/media/ssh/

# Verificar permisos (deben ser 600)
ls -l /opt/base/app/diaken/media/ssh/*.pem
```

**Permisos correctos:**
```
-rw------- 1 diaken diaken 1234 Nov 29 16:00 my_key.pem
```

**Permisos incorrectos (se corrigen automáticamente):**
```
-rw-r--r-- 1 diaken diaken 1234 Nov 29 16:00 my_key.pem  # ❌ Demasiado permisivo
```

**Corregir manualmente si es necesario:**
```bash
chmod 600 /opt/base/app/diaken/media/ssh/*.pem
```

---

### ✅ 3. Verificar conectividad de red

```bash
# Desde el servidor Diaken, hacer ping a la VM
ping -c 4 10.100.18.79

# Verificar que el puerto 22 está abierto
nc -zv 10.100.18.79 22

# O usar telnet
telnet 10.100.18.79 22
```

**Resultado esperado:**
```
Connection to 10.100.18.79 22 port [tcp/ssh] succeeded!
```

**Si falla:**
- La VM no tiene red configurada
- El firewall está bloqueando el puerto 22
- La VM no arrancó correctamente

---

### ✅ 4. Verificar que SSH está habilitado en la plantilla

La plantilla de VM debe tener:
- ✅ SSH server instalado (`openssh-server`)
- ✅ SSH habilitado al arranque
- ✅ Puerto 22 abierto en firewall de la VM

**Para RedHat/CentOS:**
```bash
# Dentro de la VM plantilla
sudo systemctl enable sshd
sudo systemctl start sshd
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

**Para Debian/Ubuntu:**
```bash
# Dentro de la VM plantilla
sudo systemctl enable ssh
sudo systemctl start ssh
sudo ufw allow 22/tcp
```

---

### ✅ 5. Verificar credenciales SSH en Diaken

1. Ve a: **Settings → Deployment Credentials**
2. Verifica que existe una credencial configurada
3. Verifica que la ruta de la llave SSH es correcta
4. Verifica que el usuario SSH es correcto (ej: `root`, `ansible`, `admin`)

**Campos importantes:**
- **Name:** Nombre descriptivo
- **SSH User:** Usuario para conectar (ej: `root`)
- **SSH Key File Path:** Ruta a la llave privada (ej: `media/ssh/my_key.pem`)

---

### ✅ 6. Verificar logs de Celery

```bash
# Ver logs en tiempo real
sudo tail -f /var/log/diaken/celery/worker.log

# Buscar errores específicos
sudo grep -i "ssh" /var/log/diaken/celery/worker.log | tail -20
sudo grep -i "error" /var/log/diaken/celery/worker.log | tail -20
```

**Logs útiles que verás:**
```
[CELERY-LINUX-xxx] Waiting for SSH on 10.100.18.79:22 (max 120s)...
[CELERY-LINUX-xxx] Still waiting for SSH... (15s/120s)
[CELERY-LINUX-xxx] Still waiting for SSH... (30s/120s)
[CELERY-LINUX-xxx] ✓ SSH ready on 10.100.18.79:22 after 45s
```

**O errores:**
```
[CELERY-LINUX-xxx] SSH key not found: /path/to/key.pem
[CELERY-LINUX-xxx] SSH key has incorrect permissions: 0o644. Fixing to 600...
[CELERY-LINUX-xxx] SSH check error: Connection refused (60s/120s)
```

---

### ✅ 7. Probar conexión SSH manualmente

```bash
# Desde el servidor Diaken
ssh -i /opt/base/app/diaken/media/ssh/my_key.pem \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    root@10.100.18.79

# Si funciona, el problema no es SSH
# Si falla, ver el error específico
```

**Errores comunes:**

**1. Permission denied (publickey)**
```
# La llave SSH no coincide con la autorizada en la VM
# Solución: Verificar que la llave pública está en ~/.ssh/authorized_keys de la VM
```

**2. Connection refused**
```
# SSH no está corriendo en la VM
# Solución: Arrancar SSH en la VM o verificar que la plantilla tiene SSH habilitado
```

**3. Connection timed out**
```
# No hay conectividad de red
# Solución: Verificar red de la VM, gateway, firewall
```

**4. Bad permissions**
```
# Los permisos de la llave son incorrectos
# Solución: chmod 600 /path/to/key.pem
```

---

## 🔍 Diagnóstico Avanzado

### Ver qué está pasando en la VM

Si tienes acceso a la consola de vCenter:

1. **Abrir consola de la VM en vCenter**
2. **Verificar que arrancó correctamente**
3. **Verificar red:**
   ```bash
   ip addr show
   ip route show
   ping 8.8.8.8
   ```
4. **Verificar SSH:**
   ```bash
   systemctl status sshd  # RedHat
   systemctl status ssh   # Debian
   ss -tlnp | grep 22
   ```

---

### Verificar configuración de red de la VM

```bash
# Desde la consola de la VM
ip addr show

# Debe mostrar la IP configurada:
# inet 10.100.18.79/24 brd 10.100.18.255 scope global ens192
```

Si la IP no está configurada:
- El playbook de Ansible no se ejecutó
- La configuración de red falló
- La VM no tiene las herramientas de VMware instaladas

---

### Verificar que la plantilla tiene cloud-init o VMware Tools

Para que Ansible pueda configurar la red, la VM debe tener:

**Opción 1: VMware Tools**
```bash
# Verificar en la VM
vmware-toolbox-cmd -v
```

**Opción 2: Cloud-init**
```bash
# Verificar en la VM
cloud-init --version
```

Si no tiene ninguno, el aprovisionamiento de red puede fallar.

---

## 🛠️ Soluciones Comunes

### Solución 1: Llave SSH incorrecta

```bash
# 1. Generar nueva llave SSH
ssh-keygen -t rsa -b 4096 -f /opt/base/app/diaken/media/ssh/diaken_key.pem -N ""

# 2. Copiar llave pública a la plantilla de VM
ssh-copy-id -i /opt/base/app/diaken/media/ssh/diaken_key.pem.pub root@TEMPLATE_IP

# 3. Configurar en Diaken (Settings → Deployment Credentials)
#    SSH Key File Path: media/ssh/diaken_key.pem
```

---

### Solución 2: SSH no habilitado en plantilla

```bash
# Conectar a la plantilla de VM
ssh root@TEMPLATE_IP

# Habilitar SSH
sudo systemctl enable sshd  # RedHat
sudo systemctl start sshd
sudo systemctl enable ssh   # Debian
sudo systemctl start ssh

# Abrir firewall
sudo firewall-cmd --permanent --add-service=ssh  # RedHat
sudo firewall-cmd --reload
sudo ufw allow 22/tcp  # Debian

# Apagar la VM y convertir a plantilla
sudo shutdown -h now
```

---

### Solución 3: Aumentar tiempo de espera

Si la VM tarda más de 120 segundos en arrancar:

```python
# Editar: /opt/base/app/diaken/deploy/tasks.py
# Línea ~656

max_wait_boot = 300  # Cambiar de 120 a 300 (5 minutos)
```

Luego reiniciar Celery:
```bash
sudo systemctl restart celery
```

---

### Solución 4: Red no configurada en la VM

Si la VM arranca pero no tiene red:

1. **Verificar que la plantilla tiene VMware Tools instalados**
2. **Verificar que el playbook de Ansible está configurando la red correctamente**
3. **Verificar que los parámetros de red son correctos:**
   - IP
   - Gateway
   - Netmask
   - Interface (ej: `ens192`, `eth0`)

---

## 📊 Logs y Monitoreo

### Ver logs de Celery en tiempo real

```bash
# Terminal 1: Logs de Celery
sudo tail -f /var/log/diaken/celery/worker.log

# Terminal 2: Logs del sistema
sudo journalctl -u celery -f

# Terminal 3: Intentar deploy
# Ir a la interfaz web y hacer deploy
```

---

### Ver historial de deployments

1. Ve a: **History → Deployment History**
2. Busca el deployment fallido
3. Haz clic en "View Details"
4. Revisa el output de Ansible

---

## 🔐 Seguridad

### Permisos correctos de archivos

```bash
# Llave SSH privada
chmod 600 /opt/base/app/diaken/media/ssh/*.pem
chown diaken:diaken /opt/base/app/diaken/media/ssh/*.pem

# Directorio SSH
chmod 700 /opt/base/app/diaken/media/ssh
chown diaken:diaken /opt/base/app/diaken/media/ssh
```

---

### Verificar que Celery puede leer la llave

```bash
# Ejecutar como usuario diaken
su - diaken
cat /opt/base/app/diaken/media/ssh/my_key.pem

# Si da error de permisos, corregir:
sudo chown diaken:diaken /opt/base/app/diaken/media/ssh/my_key.pem
sudo chmod 600 /opt/base/app/diaken/media/ssh/my_key.pem
```

---

## 📞 Soporte

Si después de seguir todos estos pasos el problema persiste:

1. **Recolectar información:**
   ```bash
   # Logs de Celery
   sudo tail -100 /var/log/diaken/celery/worker.log > celery.log
   
   # Estado de servicios
   sudo systemctl status redis celery > services.log
   
   # Prueba de conectividad
   ping -c 4 10.100.18.79 > connectivity.log
   nc -zv 10.100.18.79 22 >> connectivity.log
   ```

2. **Abrir issue en GitHub:**
   - https://github.com/htheran/diaken-free/issues
   - Adjuntar logs recolectados
   - Describir el problema paso a paso

---

## ✅ Checklist Final

Antes de intentar otro deploy, verifica:

- [ ] Redis está corriendo: `sudo systemctl status redis`
- [ ] Celery está corriendo: `sudo systemctl status celery`
- [ ] Llave SSH existe: `ls -la /opt/base/app/diaken/media/ssh/`
- [ ] Permisos correctos: `ls -l /opt/base/app/diaken/media/ssh/*.pem` (debe ser 600)
- [ ] Credencial configurada en Diaken (Settings → Deployment Credentials)
- [ ] Plantilla tiene SSH habilitado
- [ ] Plantilla tiene VMware Tools o cloud-init
- [ ] Red de la VM es accesible desde Diaken
- [ ] Puerto 22 está abierto: `nc -zv VM_IP 22`

---

**¡Buena suerte con tus deployments!** 🚀
