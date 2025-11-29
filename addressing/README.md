# Addressing App - VM IP/MAC Inventory

## 📋 Descripción

App para consultar y buscar información de red (IP, MAC, hostname, OS) de máquinas virtuales desde vCenter.

**Características principales**:
- ✅ Consulta en tiempo real desde vCenter (no almacena en BD)
- ✅ Selector de vCenter con opción "---------------" por defecto
- ✅ Búsqueda por IP, MAC o hostname
- ✅ Paginación (50 VMs por página)
- ✅ Exportación a CSV
- ✅ Soporte para múltiples IPs y MACs por VM
- ✅ Indicador de estado de energía (ON/OFF/SUSPENDED)

---

## 🏗️ Arquitectura

### Sin Base de Datos Propia
Esta app **NO almacena** datos de VMs en la base de datos. Todo se consulta en tiempo real desde vCenter usando PyVmomi.

**Ventajas**:
- Siempre datos actualizados
- No requiere sincronización
- No consume espacio en BD
- Ideal para inventario dinámico

### Usa VCenterCredential de Settings
Los vCenters se gestionan desde la app `settings` (modelo `VCenterCredential`).

---

## 🔧 Componentes

### 1. Modelos (`models.py`)
**No tiene modelos propios**. Usa `VCenterCredential` de la app `settings`.

### 2. Servicio vCenter (`vcenter_service.py`)

#### Clase `VCenterService`
```python
service = VCenterService(
    host='vcenter.example.com',
    port=443,
    user='administrator@vsphere.local',
    pwd='password',
    disable_ssl_verification=True
)

service.connect()
vms = service.get_all_vms()
service.disconnect()
```

**Métodos**:
- `connect()`: Establece conexión con vCenter
- `disconnect()`: Cierra conexión
- `get_all_vms()`: Obtiene todas las VMs con sus datos de red
- `search_vms(query, field)`: Busca VMs por IP, MAC o hostname

#### Función Helper
```python
vms = get_vcenter_vms(
    vcenter_config={'host': '...', 'port': 443, ...},
    search_query='10.100.9',
    search_field='ip'
)
```

### 3. Vistas (`views.py`)

#### `vm_list(request)`
Vista principal que muestra el listado de VMs.

**Parámetros GET**:
- `vcenter`: ID del vCenter seleccionado
- `search`: Texto de búsqueda
- `search_field`: Campo donde buscar (`all`, `ip`, `mac`, `hostname`)
- `page`: Número de página

#### `export_csv(request)`
Exporta los resultados a CSV.

**Formato CSV**:
```
VM Name,Hostname,IP Address,MAC Address,Operating System,Power State,Additional IPs,Additional MACs
```

### 4. Templates (`templates/addressing/`)

#### `vm_list.html`
- Selector de vCenter (con "---------------" por defecto)
- Campo de búsqueda con selector de campo
- Tabla con resultados paginados
- Botón de exportar CSV
- Indicadores visuales de estado

---

## 🚀 Uso

### Acceder a la App
```
http://servidor/addressing/
```

### Flujo de Uso

1. **Seleccionar vCenter**
   - Elegir de la lista desplegable
   - Al seleccionar, se cargan automáticamente las VMs

2. **Buscar** (opcional)
   - Seleccionar campo: All Fields, IP, MAC, Hostname
   - Ingresar texto de búsqueda
   - Click en "Search"

3. **Ver Resultados**
   - Tabla paginada con 50 VMs por página
   - Múltiples IPs/MACs se muestran en lista
   - Estado de energía con colores

4. **Exportar** (opcional)
   - Click en "Export CSV"
   - Descarga archivo con todos los resultados

---

## 📊 Datos Retornados por VM

```python
{
    'vm_name': 'VM-PROD-01',
    'hostname': 'server01.example.com',
    'ips': ['10.100.9.10', '192.168.1.10'],
    'macs': ['00:50:56:xx:xx:xx', '00:50:56:yy:yy:yy'],
    'os': 'Microsoft Windows Server 2019 (64-bit)',
    'power_state': 'poweredOn',
    'ip_primary': '10.100.9.10',
    'mac_primary': '00:50:56:xx:xx:xx'
}
```

---

## 🔍 Búsqueda

### Por IP
```
Buscar: 10.100.9
Campo: IP Address
```
Encuentra todas las VMs con IPs que contengan "10.100.9"

### Por MAC
```
Buscar: 00:50:56
Campo: MAC Address
```
Encuentra todas las VMs con MACs que contengan "00:50:56"

### Por Hostname
```
Buscar: prod
Campo: Hostname
```
Encuentra todas las VMs con hostname que contenga "prod"

### En Todos los Campos
```
Buscar: server
Campo: All Fields
```
Busca en IP, MAC y hostname simultáneamente

---

## 🔐 Seguridad

### Autenticación
- Requiere login (`@login_required`)
- Solo usuarios autenticados pueden acceder

### Credenciales vCenter
- Almacenadas en `VCenterCredential` (settings app)
- Contraseñas encriptadas con `EncryptedCredentialMixin`
- Desencriptadas solo en memoria durante la conexión

### SSL
- Soporta verificación SSL o deshabilitarla
- Configurado por vCenter en `VCenterCredential.ssl_verify`

---

## ⚙️ Configuración

### Agregar vCenter

Desde Django Admin o Settings:

```python
from settings.models import VCenterCredential

vcenter = VCenterCredential.objects.create(
    name='vCenter Production',
    host='vcenter.example.com',
    user='administrator@vsphere.local',
    password='secure_password',  # Se encripta automáticamente
    ssl_verify=False
)
```

### Ajustar Paginación

En `views.py`, línea 74:
```python
paginator = Paginator(vms, 50)  # Cambiar 50 por el número deseado
```

---

## 🐛 Troubleshooting

### Error: "Error al conectar a vCenter"

**Causas posibles**:
1. vCenter no accesible desde el servidor
2. Credenciales incorrectas
3. Puerto 443 bloqueado por firewall
4. Certificado SSL inválido (si ssl_verify=True)

**Solución**:
```bash
# Probar conectividad
telnet vcenter.example.com 443

# Verificar credenciales en settings
python manage.py shell
>>> from settings.models import VCenterCredential
>>> vc = VCenterCredential.objects.first()
>>> vc.get_password()  # Verificar que desencripta correctamente
```

### Error: "No VMs found"

**Causas posibles**:
1. vCenter sin VMs
2. VMs sin información de red
3. Búsqueda muy específica

**Solución**:
- Verificar que las VMs tengan VMware Tools instalado
- Limpiar filtros de búsqueda
- Verificar que las VMs estén encendidas

### Rendimiento Lento

**Causas**:
- vCenter con muchas VMs (>1000)
- Red lenta entre servidor y vCenter
- vCenter sobrecargado

**Soluciones**:
1. Usar búsqueda para filtrar
2. Considerar caché (implementación futura)
3. Aumentar timeout en `vcenter_service.py`

---

## 📈 Mejoras Futuras

- [ ] Caché de resultados (Redis)
- [ ] Filtros avanzados (por datacenter, cluster, resource pool)
- [ ] Exportar a Excel con formato
- [ ] Gráficos de uso de IPs
- [ ] Detección de IPs duplicadas
- [ ] Historial de cambios de IP/MAC
- [ ] API REST para integración

---

## 📝 Notas

- **PyVmomi**: Requiere `pyvmomi` instalado (`pip install pyvmomi`)
- **Timeout**: Conexiones a vCenter tienen timeout de 30 segundos por defecto
- **Filtrado**: Las IPs link-local (169.254.x.x) y IPv6 link-local (fe80::) se filtran automáticamente
- **VMs sin red**: VMs sin IPs ni MACs no se muestran en los resultados

---

## 👥 Autor

Creado para Diaken-PDN
Fecha: 2025-11-09
