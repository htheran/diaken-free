# 🌐 Network-Based ALLOWED_HOSTS - Documentación

**Fecha:** 16 de Octubre, 2025  
**Versión:** 1.0

---

## 📋 Descripción

Este middleware personalizado extiende la funcionalidad de `ALLOWED_HOSTS` de Django para soportar rangos de red CIDR (por ejemplo, `10.104.10.0/24`) en lugar de solo IPs individuales.

### Ventajas

✅ **Gestión Simplificada:** Permite toda una red en lugar de IPs individuales  
✅ **Escalabilidad:** Fácil de mantener cuando se agregan nuevos hosts  
✅ **Seguridad:** Mantiene la validación de Host header de Django  
✅ **Flexibilidad:** Soporta múltiples rangos de red simultáneamente  

---

## 🔧 Configuración

### Archivo: `.env`

Agrega la variable `DJANGO_ALLOWED_NETWORKS` con rangos CIDR separados por comas:

```bash
# Allowed Networks (CIDR ranges)
DJANGO_ALLOWED_NETWORKS=10.104.10.0/24,10.100.5.0/24,192.168.1.0/24
```

### Ejemplos de Configuración

#### Ejemplo 1: Red Interna Única
```bash
DJANGO_ALLOWED_NETWORKS=10.104.10.0/24
```
**Permite:** Todas las IPs desde `10.104.10.1` hasta `10.104.10.254`

#### Ejemplo 2: Múltiples Redes
```bash
DJANGO_ALLOWED_NETWORKS=10.104.10.0/24,10.100.5.0/24,192.168.1.0/24
```
**Permite:**
- Red 1: `10.104.10.0/24` (256 IPs)
- Red 2: `10.100.5.0/24` (256 IPs)
- Red 3: `192.168.1.0/24` (256 IPs)

#### Ejemplo 3: Red Más Grande
```bash
DJANGO_ALLOWED_NETWORKS=10.0.0.0/8
```
**Permite:** Todas las IPs desde `10.0.0.0` hasta `10.255.255.255` (16,777,216 IPs)

⚠️ **Advertencia:** Redes muy grandes (como `/8`) pueden ser inseguras. Usa el rango más pequeño posible.

---

## 📁 Archivos Modificados

### 1. `security_fixes/network_allowed_hosts.py`
Middleware personalizado que valida rangos de red CIDR.

**Ubicación:** `/opt/www/app/diaken-pdn/security_fixes/network_allowed_hosts.py`

**Funciones principales:**
- `NetworkAllowedHostsMiddleware`: Middleware principal
- `_load_allowed_networks()`: Carga rangos de red desde settings
- `_is_ip_in_allowed_networks()`: Valida si una IP está en un rango permitido

### 2. `diaken/settings_production.py`
Configuración de Django actualizada.

**Cambios:**
- Agregada variable `ALLOWED_NETWORKS`
- Agregado middleware `NetworkAllowedHostsMiddleware`
- Fallback por defecto: `['10.104.10.0/24', '10.100.5.0/24']`

### 3. `.env` y `.env.example`
Variables de entorno actualizadas.

**Nueva variable:**
```bash
DJANGO_ALLOWED_NETWORKS=10.104.10.0/24,10.100.5.0/24
```

---

## 🔍 Cómo Funciona

### Flujo de Validación

1. **Petición HTTP llega al servidor**
   - Ejemplo: `GET / HTTP/1.1` con `Host: 10.104.10.50`

2. **NetworkAllowedHostsMiddleware se ejecuta primero**
   - Extrae el host header: `10.104.10.50`
   - Verifica si es una IP válida
   - Comprueba si está en algún rango CIDR permitido

3. **Si está en un rango permitido:**
   - ✅ Marca la petición como validada
   - ✅ Permite que continúe al siguiente middleware
   - ✅ Django procesa la petición normalmente

4. **Si NO está en un rango permitido:**
   - Pasa la validación a `ALLOWED_HOSTS` estándar de Django
   - Django valida contra hostnames/IPs individuales
   - Si tampoco coincide → HTTP 400 Bad Request

### Ejemplo de Validación

**Configuración:**
```bash
DJANGO_ALLOWED_HOSTS=your-server.example.com,localhost
DJANGO_ALLOWED_NETWORKS=10.104.10.0/24,10.100.5.0/24
```

**Peticiones:**

| Host Header | ¿En ALLOWED_NETWORKS? | ¿En ALLOWED_HOSTS? | Resultado |
|-------------|----------------------|-------------------|-----------|
| `10.104.10.50` | ✅ Sí (`10.104.10.0/24`) | - | ✅ Permitido |
| `10.100.5.100` | ✅ Sí (`10.100.5.0/24`) | - | ✅ Permitido |
| `your-server.example.com` | ❌ No es IP | ✅ Sí | ✅ Permitido |
| `localhost` | ❌ No es IP | ✅ Sí | ✅ Permitido |
| `10.200.1.50` | ❌ No | ❌ No | ❌ Rechazado (400) |
| `evil.com` | ❌ No | ❌ No | ❌ Rechazado (400) |

---

## 🛠️ Modificar Rangos de Red

### Opción 1: Editar `.env` (Recomendado)

**Archivo:** `/opt/www/app/diaken-pdn/.env`

```bash
# Editar esta línea:
DJANGO_ALLOWED_NETWORKS=10.104.10.0/24,10.100.5.0/24

# Agregar nuevas redes:
DJANGO_ALLOWED_NETWORKS=10.104.10.0/24,10.100.5.0/24,192.168.1.0/24
```

**Reiniciar Apache:**
```bash
sudo systemctl restart httpd
```

### Opción 2: Editar `settings_production.py`

**Archivo:** `/opt/www/app/diaken-pdn/diaken/settings_production.py`

Buscar la sección:
```python
# SECURITY: Allowed networks (CIDR ranges)
ALLOWED_NETWORKS_STR = os.environ.get('DJANGO_ALLOWED_NETWORKS', '')
if ALLOWED_NETWORKS_STR:
    ALLOWED_NETWORKS = [network.strip() for network in ALLOWED_NETWORKS_STR.split(',') if network.strip()]
else:
    # Fallback: Allow common internal networks
    ALLOWED_NETWORKS = ['10.104.10.0/24', '10.100.5.0/24']  # ← Modificar aquí
```

**Reiniciar Apache:**
```bash
sudo systemctl restart httpd
```

---

## 🧪 Probar la Configuración

### Desde el Servidor

```bash
# Probar con IP en rango permitido
curl -I -k -H "Host: 10.104.10.50" https://localhost/

# Probar con IP fuera de rango
curl -I -k -H "Host: 10.200.1.50" https://localhost/

# Probar con hostname
curl -I -k https://your-server.example.com/
```

### Desde el Navegador

1. Acceder a: `https://10.104.10.30/`
   - Debe funcionar ✅ (está en `10.104.10.0/24`)

2. Acceder a: `https://10.100.5.89/`
   - Debe funcionar ✅ (está en `10.100.5.0/24`)

3. Acceder a: `https://your-server.example.com/`
   - Debe funcionar ✅ (en ALLOWED_HOSTS)

---

## 📊 Rangos de Red Comunes

| Notación CIDR | Rango de IPs | Número de IPs | Uso Común |
|---------------|--------------|---------------|-----------|
| `10.104.10.0/24` | `10.104.10.1` - `10.104.10.254` | 254 | Red departamental |
| `10.104.0.0/16` | `10.104.0.1` - `10.104.255.254` | 65,534 | Red de edificio |
| `10.0.0.0/8` | `10.0.0.1` - `10.255.255.254` | 16,777,214 | Red corporativa completa |
| `192.168.1.0/24` | `192.168.1.1` - `192.168.1.254` | 254 | Red local pequeña |
| `172.16.0.0/12` | `172.16.0.1` - `172.31.255.254` | 1,048,574 | Red privada mediana |

---

## 🔒 Consideraciones de Seguridad

### ✅ Buenas Prácticas

1. **Usa el rango más pequeño posible**
   - ✅ `10.104.10.0/24` (254 IPs)
   - ❌ `10.0.0.0/8` (16M IPs)

2. **Combina con ALLOWED_HOSTS**
   - Usa `ALLOWED_NETWORKS` para IPs internas
   - Usa `ALLOWED_HOSTS` para hostnames públicos

3. **Documenta los rangos**
   - Anota qué red representa cada rango CIDR
   - Mantén actualizada la documentación

4. **Revisa periódicamente**
   - Elimina rangos que ya no se usan
   - Ajusta según cambios en la red

### ⚠️ Advertencias

- **NO uses `0.0.0.0/0`**: Permite TODAS las IPs (inseguro)
- **NO uses rangos públicos**: Solo redes privadas internas
- **Cuidado con rangos grandes**: Más IPs = mayor superficie de ataque

---

## 🐛 Troubleshooting

### Problema: Sigue rechazando IPs en el rango

**Solución:**
1. Verificar que el `.env` tiene la configuración correcta
2. Reiniciar Apache completamente: `sudo systemctl restart httpd`
3. Verificar logs: `sudo tail -f /opt/www/logs/apache_error.log`

### Problema: No carga el middleware

**Solución:**
1. Verificar que `security_fixes/network_allowed_hosts.py` existe
2. Verificar que está en `MIDDLEWARE` en `settings_production.py`
3. Verificar sintaxis Python: `python3.12 manage.py check`

### Problema: Error al parsear CIDR

**Solución:**
1. Verificar formato correcto: `10.104.10.0/24` (sin espacios)
2. Verificar que la máscara es válida (`/8` a `/32`)
3. Ver logs para mensajes de error específicos

---

## 📞 Soporte

Para problemas o preguntas:

1. Revisar esta documentación
2. Verificar logs: `/opt/www/logs/apache_error.log`
3. Ejecutar: `python3.12 manage.py check`
4. Revisar configuración en `.env`

---

**Última actualización:** 16 de Octubre, 2025  
**Mantenedor:** Equipo de Seguridad Diaken  
**Versión:** 1.0
