# 📋 Guía de Logs y Diagnóstico - Proyecto Diaken

**Última actualización:** 16 de Octubre, 2025

---

## 📁 Ubicación de Logs

### 1. Apache Access Log (Peticiones HTTP/HTTPS)

**Archivo:** `/opt/www/logs/apache_access.log`

**Ver últimas 20 líneas:**
```bash
sudo tail -20 /opt/www/logs/apache_access.log
```

**Ver en tiempo real:**
```bash
sudo tail -f /opt/www/logs/apache_access.log
```

**Formato:** Cada línea muestra:
- IP del cliente
- Fecha y hora
- Método HTTP y URL
- Código de respuesta (200, 302, 400, 500, etc.)
- User-Agent del navegador

---

### 2. Apache Error Log (Errores de Apache y Django)

**Archivo:** `/opt/www/logs/apache_error.log`

**Ver últimas 50 líneas:**
```bash
sudo tail -50 /opt/www/logs/apache_error.log
```

**Ver en tiempo real:**
```bash
sudo tail -f /opt/www/logs/apache_error.log
```

**Buscar errores específicos:**
```bash
sudo grep -i "error" /opt/www/logs/apache_error.log | tail -20
sudo grep -i "400\|bad request" /opt/www/logs/apache_error.log | tail -20
```

---

### 3. Systemd Logs (Logs del servicio httpd)

**Ver últimas 50 líneas:**
```bash
sudo journalctl -u httpd -n 50 --no-pager
```

**Ver en tiempo real:**
```bash
sudo journalctl -u httpd -f
```

**Ver solo errores:**
```bash
sudo journalctl -u httpd -p err --no-pager
```

---

## 🔍 Comandos de Diagnóstico

### Verificar Estado de Servicios

```bash
# Estado de Apache
sudo systemctl status httpd

# Estado de diaken.service
sudo systemctl status diaken

# Verificar si Apache está escuchando en puertos 80 y 443
sudo ss -tulpn | grep -E ":80|:443"
```

### Verificar Configuración de Apache

```bash
# Verificar sintaxis de configuración
sudo httpd -t

# Ver configuración cargada
sudo httpd -S
```

### Probar Conexiones

```bash
# Probar HTTP (debe redirigir a HTTPS)
curl -I http://localhost/

# Probar HTTPS
curl -I -k https://localhost/

# Probar con hostname
curl -I -k https://your-server.example.com/
```

---

## 🐛 Diagnóstico de Error 400 Bad Request

### Causas Comunes

1. **ALLOWED_HOSTS no configurado correctamente**
   - Django rechaza peticiones si el Host header no está en ALLOWED_HOSTS

2. **CSRF_TRUSTED_ORIGINS no configurado**
   - Django rechaza peticiones HTTPS si la URL no está en CSRF_TRUSTED_ORIGINS

3. **Variables de entorno no cargadas**
   - Apache no está cargando `/etc/httpd/conf.d/diaken-env.conf`

### Verificar Variables de Entorno

```bash
# Ver contenido de diaken-env.conf
sudo cat /etc/httpd/conf.d/diaken-env.conf

# Verificar que está siendo incluido
sudo grep -r "Include.*diaken-env" /etc/httpd/conf.d/
```

### Verificar ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS

Ejecutar desde el servidor:

```bash
python3.12 << 'PYEOF'
import os
import sys

os.environ['DJANGO_SECRET_KEY'] = 'jvvs6z!io)#oc577g71wk##(ipqyev+o(#k*r=bhgcwr^y-0q!'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'your-server.example.com,localhost,127.0.0.1,10.100.5.89,10.104.10.30,10.104.10.20'
os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = 'https://your-server.example.com,http://your-server.example.com,https://localhost,http://localhost,https://10.100.5.89,http://10.100.5.89,https://10.104.10.30,http://10.104.10.30,https://10.104.10.20,http://10.104.10.20'
os.environ['ENCRYPTION_KEY'] = '3zQByYszXlilsYYNXJcRxYbUxlHb9racTj_rXkyukO4='
os.environ['DJANGO_SETTINGS_MODULE'] = 'diaken.settings_production'

sys.path.insert(0, '/opt/www/app/diaken-pdn')

import django
django.setup()

from django.conf import settings

print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
print("\nCSRF_TRUSTED_ORIGINS:", settings.CSRF_TRUSTED_ORIGINS)
PYEOF
```

---

## 🔧 Soluciones Comunes

### Solución 1: Reiniciar Apache Completamente

```bash
sudo systemctl restart httpd
```

**Nota:** `reload` solo recarga la configuración, `restart` reinicia completamente el servicio.

### Solución 2: Limpiar Caché del Navegador

1. Presiona **Ctrl+Shift+Delete** (Windows) o **Cmd+Shift+Delete** (Mac)
2. Borra caché y cookies
3. Cierra y abre el navegador
4. Intenta de nuevo

### Solución 3: Usar Ventana de Incógnito

1. Abre una ventana de incógnito/privada
2. Accede a la URL
3. Esto evita problemas de caché

### Solución 4: Acceder por el Hostname Correcto

**CORRECTO:**
- `https://your-server.example.com/`

**PUEDE CAUSAR PROBLEMAS:**
- `https://10.104.10.30/` (certificado no coincide)

---

## 📊 Interpretación de Códigos de Respuesta HTTP

| Código | Significado | Causa Común |
|--------|-------------|-------------|
| 200 | OK | Petición exitosa |
| 301 | Moved Permanently | Redirect HTTP → HTTPS |
| 302 | Found | Redirect a /login/ (Django) |
| 400 | Bad Request | ALLOWED_HOSTS o CSRF_TRUSTED_ORIGINS |
| 403 | Forbidden | Permisos de archivos |
| 404 | Not Found | URL no existe |
| 500 | Internal Server Error | Error de Python/Django |
| 502 | Bad Gateway | WSGI no responde |
| 503 | Service Unavailable | Apache no puede conectar a WSGI |

---

## 🚨 Troubleshooting Paso a Paso

### Paso 1: Verificar que Apache está corriendo

```bash
sudo systemctl status httpd
```

**Debe mostrar:** `Active: active (running)`

### Paso 2: Verificar logs de acceso

```bash
sudo tail -10 /opt/www/logs/apache_access.log
```

**Buscar:** Código de respuesta (último número antes del user-agent)

### Paso 3: Verificar logs de error

```bash
sudo tail -30 /opt/www/logs/apache_error.log
```

**Buscar:** Mensajes de error de Python o Django

### Paso 4: Probar desde el servidor

```bash
curl -I -k https://localhost/
```

**Debe devolver:** `HTTP/1.1 302 Found` y `Location: /login/?next=/`

### Paso 5: Verificar variables de entorno

```bash
sudo cat /etc/httpd/conf.d/diaken-env.conf
```

**Verificar que contiene:**
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `ENCRYPTION_KEY`

### Paso 6: Reiniciar Apache

```bash
sudo systemctl restart httpd
```

### Paso 7: Probar de nuevo desde el navegador

Acceder a: `https://your-server.example.com/`

---

## 📝 Checklist de Diagnóstico

- [ ] Apache está corriendo (`systemctl status httpd`)
- [ ] Puertos 80 y 443 están abiertos (`ss -tulpn | grep -E ":80|:443"`)
- [ ] Configuración de Apache es válida (`httpd -t`)
- [ ] Variables de entorno están configuradas (`cat /etc/httpd/conf.d/diaken-env.conf`)
- [ ] `diaken-env.conf` está siendo incluido (`grep -r "Include.*diaken-env" /etc/httpd/conf.d/`)
- [ ] Localhost funciona (`curl -I -k https://localhost/`)
- [ ] Logs no muestran errores críticos (`tail /opt/www/logs/apache_error.log`)
- [ ] Caché del navegador está limpia
- [ ] Accediendo por hostname correcto (`https://your-server.example.com/`)

---

## 🆘 Si Nada Funciona

1. **Capturar logs en tiempo real:**
   ```bash
   sudo tail -f /opt/www/logs/apache_error.log
   ```

2. **En otra terminal, hacer la petición:**
   ```bash
   curl -I -k https://your-server.example.com/
   ```

3. **Observar qué error aparece en el log**

4. **Compartir el error exacto para diagnóstico**

---

## 📞 Contacto y Soporte

Para problemas persistentes:

1. Revisar esta guía completa
2. Ejecutar todos los comandos de diagnóstico
3. Capturar logs relevantes
4. Documentar el problema con detalles específicos

---

**Última actualización:** 16 de Octubre, 2025  
**Mantenedor:** Equipo de Seguridad Diaken  
**Estado:** ✅ PRODUCTION READY
