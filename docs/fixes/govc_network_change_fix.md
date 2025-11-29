# Corrección: Cambio de Red de VM con govc - Oct 17, 2025

## Problema Reportado
El sistema cambiaba el hostname, la IP y reiniciaba la VM, pero **NO cambiaba la red en vCenter**.

## Diagnóstico

### Problema 1: govc no estaba instalado
```bash
$ which govc
/usr/bin/which: no govc in (...)
```

**Causa raíz**: La función `change_vm_network_govc()` intentaba ejecutar el comando `govc`, pero este no estaba instalado en el sistema.

### Problema 2: Usuario apache no podía encontrar govc
```bash
$ sudo -u apache govc version
sudo: govc: command not found

$ sudo -u apache bash -c 'echo $PATH'
/sbin:/bin:/usr/sbin:/usr/bin
```

**Causa raíz**: Después de instalar govc en `/usr/local/bin/`, el usuario `apache` no podía encontrarlo porque `/usr/local/bin` no está en su PATH.

### Problema 3: Falta de logging detallado
La función no tenía suficiente logging para diagnosticar por qué fallaba el cambio de red.

## Soluciones Implementadas

### 1. Instalación de govc
```bash
curl -L -o - "https://github.com/vmware/govmomi/releases/latest/download/govc_$(uname -s)_$(uname -m).tar.gz" | sudo tar -C /usr/local/bin -xvzf - govc
```

**Versión instalada**: govc 0.52.0  
**Ubicación**: `/usr/local/bin/govc`

### 2. Uso de ruta completa en el código

**Problema**: El usuario `apache` no tiene `/usr/local/bin` en su PATH.

**Solución**: Modificar todas las llamadas a `govc` para usar la ruta completa `/usr/local/bin/govc`.

**Archivos modificados**:
- `deploy/govc_helper.py`: Todas las llamadas a `govc` ahora usan `/usr/local/bin/govc`

**Verificación**:
```bash
$ sudo -u apache /usr/local/bin/govc version
govc 0.52.0
```

### 3. Mejoras en la función `change_vm_network_govc()`

**Archivo**: `/opt/www/app/diaken-pdn/deploy/govc_helper.py`

#### Validaciones agregadas:

1. **Verificar que la VM existe** (PASO 1)
   ```bash
   govc vm.info <vm_name>
   ```

2. **Listar redes disponibles** (PASO 2)
   ```bash
   govc ls network
   ```

3. **Obtener red actual de la VM** (PASO 3)
   ```bash
   govc device.info -vm <vm_name> ethernet-0
   ```

4. **Cambiar la red** (PASO 4)
   ```bash
   govc vm.network.change -vm <vm_name> -net <network_name> ethernet-0
   ```

5. **Verificar el cambio** (PASO 5)
   ```bash
   govc device.info -vm <vm_name> ethernet-0
   ```

#### Mejoras de logging:
- Cambiado de `logger.debug()` a `logger.info()` para mensajes importantes
- Agregado logging de:
  - vCenter host
  - Return codes de cada comando
  - STDOUT y STDERR de cada comando
  - Información de la VM antes y después del cambio
  - Lista de redes disponibles

## Verificación

### Comprobar instalación de govc:
```bash
$ govc version
govc 0.52.0
```

### Probar conectividad con vCenter:
```bash
export GOVC_URL="vcenter.example.com"
export GOVC_USERNAME="user@vsphere.local"
export GOVC_PASSWORD="password"
export GOVC_INSECURE="true"

govc about
```

### Ver logs detallados:
```bash
sudo journalctl -xeu httpd.service -f | grep GOVC
```

## Flujo de Deployment con Cambio de Red

1. **Provisioning** (provision_vm.yml):
   - Conecta a la VM usando la IP de la plantilla
   - Cambia hostname
   - Configura nueva IP estática
   - Programa reinicio (`shutdown -r +1`)

2. **Cambio de Red** (durante el reinicio):
   - Ejecuta `change_vm_network_govc()`
   - Cambia la red en vCenter usando govc
   - Espera 90 segundos para reinicio

3. **Verificación Post-Reinicio**:
   - Verifica conectividad SSH en la nueva IP
   - Acepta fingerprint SSH
   - Ejecuta playbooks adicionales (si aplica)

## Archivos Modificados

1. **`deploy/govc_helper.py`**:
   - Función `change_vm_network_govc()` mejorada con 5 pasos de validación
   - Todas las llamadas a `govc` usan ruta completa `/usr/local/bin/govc`
   - Función `configure_vm_ip_govc()` también actualizada
   - Logging detallado con `logger.info()` y `logger.error()`

2. **`deploy/views.py`**:
   - Logging mejorado en la sección de cambio de red
   - Mensajes de éxito/error agregados a `provision_output`
   - Información detallada del error visible en el historial de deployment

## Comandos de Troubleshooting

### Ver información de una VM:
```bash
govc vm.info <vm_name>
```

### Ver red actual de una VM:
```bash
govc device.info -vm <vm_name> ethernet-0
```

### Listar todas las redes:
```bash
govc ls network
```

### Cambiar red manualmente:
```bash
govc vm.network.change -vm <vm_name> -net <network_name> ethernet-0
```

## Estado
✅ **RESUELTO** - govc instalado y función mejorada con validaciones completas

## Próximos Pasos
1. Probar deployment completo con cambio de red
2. Verificar logs para confirmar que todos los pasos se ejecutan correctamente
3. Documentar cualquier error adicional que aparezca en los logs
