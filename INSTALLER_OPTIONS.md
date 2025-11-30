# Diaken - Opciones de Instalación

Diaken ofrece dos opciones de instalación según tus necesidades.

## 📦 Opciones Disponibles

### 1. Instalación Standalone (install-diaken-standalone.sh)

**Características:**
- ✅ Django ejecutándose directamente en puerto 9090
- ✅ Sin proxy reverso
- ✅ Acceso HTTP directo
- ✅ Ideal para desarrollo y testing
- ✅ Configuración más simple

**Cuándo usar:**
- Entornos de desarrollo
- Testing rápido
- Ambientes internos sin exposición a internet
- Cuando no necesitas HTTPS

**Instalación:**
```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken-standalone.sh | sudo bash
```

**Acceso:**
- URL: `http://IP:9090`
- No requiere configuración SSL

---

### 2. Instalación con Nginx (install-diaken-nginx.sh) ⭐ RECOMENDADO

**Características:**
- ✅ Nginx como proxy reverso
- ✅ HTTPS con certificados SSL (self-signed por defecto)
- ✅ Optimización de seguridad
- ✅ Timeouts configurados para playbooks largos (600s)
- ✅ Headers de seguridad (HSTS, X-Frame-Options, etc.)
- ✅ Rate limiting
- ✅ Redirección automática HTTP → HTTPS
- ✅ Archivos estáticos servidos eficientemente
- ✅ Listo para producción

**Cuándo usar:**
- **Producción** (recomendado)
- Ambientes expuestos a internet
- Cuando necesitas HTTPS
- Cuando quieres máxima seguridad
- Cuando ejecutas playbooks Ansible largos

**Instalación:**
```bash
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken-nginx.sh | sudo bash
```

**Acceso:**
- URL: `https://IP`
- Redirige automáticamente desde HTTP (puerto 80)
- ⚠️ **Nota:** Usará certificado self-signed, el navegador mostrará advertencia

---

## 🔒 Configuración SSL

### Certificados Self-Signed (Por Defecto)

Ambas instalaciones con nginx incluyen certificados self-signed automáticamente:
- **Ubicación:** `/etc/nginx/ssl/diaken.crt` y `/etc/nginx/ssl/diaken.key`
- **Validez:** 365 días
- **Advertencia:** El navegador mostrará advertencia de seguridad

### Reemplazar con Certificados Válidos

Para producción, reemplaza los certificados self-signed:

#### Opción 1: Let's Encrypt (Gratis)
```bash
# Instalar certbot
sudo dnf install -y certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com

# Certbot configurará nginx automáticamente
```

#### Opción 2: Certificado Comercial
```bash
# Reemplazar certificados
sudo cp tu-certificado.crt /etc/nginx/ssl/diaken.crt
sudo cp tu-llave.key /etc/nginx/ssl/diaken.key

# Reiniciar nginx
sudo systemctl restart nginx
```

---

## ⚙️ Configuración de Nginx

### Ubicación de Archivos

- **Configuración:** `/etc/nginx/conf.d/diaken.conf`
- **Certificados SSL:** `/etc/nginx/ssl/`
- **Logs:** `/var/log/nginx/diaken_*.log`

### Características de Seguridad Implementadas

```nginx
# Timeouts optimizados para Ansible
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;

# Headers de seguridad
Strict-Transport-Security
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block

# Tamaño máximo de archivo
client_max_body_size 100M;

# Rate limiting (protección contra ataques)
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
```

### Modificar Configuración

```bash
# Editar configuración
sudo nano /etc/nginx/conf.d/diaken.conf

# Verificar sintaxis
sudo nginx -t

# Aplicar cambios
sudo systemctl reload nginx
```

---

## 🔄 Comparación

| Característica | Standalone | Con Nginx |
|----------------|------------|-----------|
| **Puerto de acceso** | 9090 | 80 → 443 |
| **Protocolo** | HTTP | HTTPS |
| **Proxy reverso** | ❌ | ✅ |
| **SSL/TLS** | ❌ | ✅ |
| **Headers de seguridad** | ❌ | ✅ |
| **Rate limiting** | ❌ | ✅ |
| **Archivos estáticos optimizados** | ❌ | ✅ |
| **Timeouts configurables** | ⚠️ Limitado | ✅ 600s |
| **Redirección HTTP→HTTPS** | ❌ | ✅ |
| **Listo para producción** | ⚠️ Desarrollo | ✅ Sí |
| **Complejidad** | Baja | Media |

---

## 🚀 Comandos Útiles

### Nginx

```bash
# Ver estado
sudo systemctl status nginx

# Reiniciar
sudo systemctl restart nginx

# Recargar configuración (sin downtime)
sudo systemctl reload nginx

# Ver logs
sudo tail -f /var/log/nginx/diaken_access.log
sudo tail -f /var/log/nginx/diaken_error.log

# Verificar configuración
sudo nginx -t
```

### Django

```bash
# Con Standalone
cd /opt/diaken
source venv/bin/activate
python manage.py runserver 0.0.0.0:9090

# Con Nginx (Django en background)
cd /opt/diaken
source venv/bin/activate
python manage.py runserver 127.0.0.1:9090
```

---

## 📊 Rendimiento

### Timeouts Configurados (Nginx)

Optimizados para playbooks Ansible largos:

- **proxy_connect_timeout:** 600s (10 minutos)
- **proxy_send_timeout:** 600s
- **proxy_read_timeout:** 600s
- **send_timeout:** 600s
- **client_body_timeout:** 300s
- **client_header_timeout:** 300s

Esto permite que playbooks que tardan varios minutos se ejecuten sin timeout.

---

## 🔐 Seguridad Adicional

### Firewall

```bash
# Habilitar firewall
sudo systemctl enable --now firewalld

# Permitir HTTPS
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### SELinux

Si usas SELinux, puede ser necesario configurar contextos:

```bash
# Permitir a nginx conectarse a Django
sudo setsebool -P httpd_can_network_connect 1

# Verificar contextos
sudo ls -lZ /etc/nginx/ssl/
```

---

## 🆘 Troubleshooting

### Nginx no inicia

```bash
# Ver logs
sudo journalctl -u nginx -n 50

# Verificar configuración
sudo nginx -t

# Verificar puertos en uso
sudo ss -tlnp | grep -E ':80|:443'
```

### Certificado SSL inválido

```bash
# Regenerar certificado self-signed
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/diaken.key \
  -out /etc/nginx/ssl/diaken.crt \
  -subj "/C=US/ST=State/L=City/O=Diaken/CN=$(hostname -f)"

sudo systemctl restart nginx
```

### Django no responde a través de Nginx

```bash
# Verificar que Django esté corriendo
curl http://127.0.0.1:9090

# Ver logs de nginx
sudo tail -f /var/log/nginx/diaken_error.log

# Verificar configuración de proxy
sudo nginx -T | grep -A 20 "location /"
```

---

## 📚 Documentación Adicional

- [INSTALLER_README.md](INSTALLER_README.md) - Guía completa del instalador
- [INSTALL_UNATTENDED.md](INSTALL_UNATTENDED.md) - Instalación desatendida
- [TROUBLESHOOTING_SSH.md](TROUBLESHOOTING_SSH.md) - Solución de problemas SSH
- [COMPONENTS.md](COMPONENTS.md) - Inventario de componentes

---

## 💡 Recomendaciones

### Para Desarrollo
✅ Usa **install-diaken-standalone.sh**
- Más rápido de configurar
- Sin complejidad de SSL
- Acceso directo al puerto 9090

### Para Producción
✅ Usa **install-diaken-nginx.sh**
- Seguridad mejorada
- HTTPS por defecto
- Optimizado para rendimiento
- Headers de seguridad
- Rate limiting

### Después de Instalar con Nginx
1. Reemplazar certificado self-signed con Let's Encrypt o comercial
2. Configurar dominio personalizado
3. Ajustar timeouts según tus playbooks
4. Configurar firewall
5. Configurar backups automatizados

---

**Versión:** 2.1.6  
**Fecha:** 2025-11-30
