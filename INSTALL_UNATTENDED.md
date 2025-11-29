# 🚀 Instalación Desatendida de Diaken

Este documento explica cómo realizar una instalación completamente automatizada de Diaken sin intervención manual.

---

## 📋 Requisitos Previos

- **Sistema Operativo:** RedHat, CentOS, Rocky Linux, Oracle Linux 9+
- **Acceso:** Usuario con privilegios sudo
- **Red:** Conexión a internet para descargar paquetes

---

## ⚡ Instalación Rápida (Desatendida)

### Opción 1: Variables de Entorno en Línea de Comando

```bash
sudo DJANGO_SUPERUSER_USERNAME=admin \
     DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123! \
     DJANGO_SUPERUSER_EMAIL=admin@example.com \
     bash <(curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh)
```

### Opción 2: Exportar Variables y Ejecutar

```bash
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123!
export DJANGO_SUPERUSER_EMAIL=admin@example.com

curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo -E bash
```

**Nota:** El flag `-E` preserva las variables de entorno.

### Opción 3: Archivo de Configuración

Crea un archivo `diaken-install.conf`:

```bash
cat > diaken-install.conf << 'EOF'
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123!
export DJANGO_SUPERUSER_EMAIL=admin@example.com
export UNATTENDED=1
EOF
```

Ejecuta la instalación:

```bash
source diaken-install.conf
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo -E bash
```

---

## 🔧 Variables de Entorno Disponibles

| Variable | Descripción | Valor por Defecto | Requerido |
|----------|-------------|-------------------|-----------|
| `DJANGO_SUPERUSER_USERNAME` | Usuario administrador de Django | `admin` | No |
| `DJANGO_SUPERUSER_PASSWORD` | Contraseña del administrador | (prompt) | Sí* |
| `DJANGO_SUPERUSER_EMAIL` | Email del administrador | (vacío) | No |
| `UNATTENDED` | Modo desatendido (salta confirmaciones) | (vacío) | No |

**\*Requerido para instalación desatendida**

---

## 📦 ¿Qué Instala el Script?

El instalador automáticamente:

1. ✅ **Instala dependencias del sistema:**
   - Python 3.12
   - Git
   - Redis
   - Compiladores y librerías

2. ✅ **Clona el proyecto:**
   - Desde GitHub: `https://github.com/htheran/diaken-free.git`
   - Directorio: `/opt/diaken`

3. ✅ **Configura Python:**
   - Crea entorno virtual
   - Instala paquetes de `requirements.txt`

4. ✅ **Configura Django:**
   - Ejecuta migraciones
   - Recolecta archivos estáticos
   - Crea superusuario

5. ✅ **Configura servicios:**
   - Redis (puerto 6379)
   - Celery Worker (systemd)
   - Diaken (systemd, opcional)

6. ✅ **Configura firewall:**
   - Abre puerto 9090

7. ✅ **Inicializa configuración:**
   - Variables globales por defecto
   - Zona horaria: America/Bogota

---

## 🔐 Seguridad

### Recomendaciones de Contraseña

Para producción, usa contraseñas seguras:

```bash
# Generar contraseña aleatoria
openssl rand -base64 32

# O usar pwgen
pwgen -s 32 1
```

### No Hardcodear Contraseñas

**❌ NO HAGAS ESTO:**
```bash
# Contraseña visible en historial de comandos
sudo DJANGO_SUPERUSER_PASSWORD=admin123 bash install.sh
```

**✅ HAZ ESTO:**
```bash
# Leer contraseña de forma segura
read -s -p "Password: " DJANGO_SUPERUSER_PASSWORD
export DJANGO_SUPERUSER_PASSWORD
sudo -E bash install-diaken.sh
```

---

## 🚀 Instalación en Producción

### Ejemplo Completo para Producción

```bash
#!/bin/bash
# production-install.sh

# Configuración
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@yourcompany.com
export UNATTENDED=1

# Solicitar contraseña de forma segura
echo "Enter Django admin password:"
read -s DJANGO_SUPERUSER_PASSWORD
export DJANGO_SUPERUSER_PASSWORD

# Ejecutar instalación
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo -E bash

# Limpiar variables sensibles
unset DJANGO_SUPERUSER_PASSWORD
```

Ejecuta:

```bash
chmod +x production-install.sh
./production-install.sh
```

---

## 🔍 Verificación Post-Instalación

Después de la instalación, verifica que todo funciona:

```bash
# 1. Verificar servicios
sudo systemctl status redis
sudo systemctl status celery

# 2. Verificar logs
sudo tail -f /var/log/diaken/celery/worker.log

# 3. Probar conexión Redis
redis-cli ping  # Debe responder: PONG

# 4. Acceder a la aplicación
# URL: http://YOUR_SERVER_IP:9090
# Usuario: admin (o el que configuraste)
# Contraseña: la que configuraste
```

---

## 🐳 Instalación con Docker (Alternativa)

Si prefieres usar Docker:

```bash
# Próximamente
# docker-compose up -d
```

---

## 🔄 Reinstalación

Si necesitas reinstalar:

```bash
# 1. Detener servicios
sudo systemctl stop celery
sudo systemctl stop redis

# 2. Eliminar instalación anterior
sudo rm -rf /opt/diaken

# 3. Ejecutar instalador nuevamente
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=NewPassword123!
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | sudo -E bash
```

---

## 📝 Logs y Troubleshooting

### Ubicación de Logs

```
/var/log/diaken/
├── celery/
│   └── worker.log          # Logs de Celery Worker
└── (otros logs)
```

### Ver Logs en Tiempo Real

```bash
# Logs de Celery
sudo tail -f /var/log/diaken/celery/worker.log

# Logs del sistema
sudo journalctl -u celery -f
sudo journalctl -u redis -f
```

### Problemas Comunes

#### Error: "Connection refused to Redis"

```bash
# Verificar que Redis está corriendo
sudo systemctl status redis

# Si no está corriendo, iniciarlo
sudo systemctl start redis
```

#### Error: "Celery worker not starting"

```bash
# Ver logs detallados
sudo journalctl -u celery -n 100

# Reiniciar servicio
sudo systemctl restart celery
```

---

## 🌐 Acceso Remoto

### Configurar Firewall para Acceso Externo

El instalador ya abre el puerto 9090, pero si usas firewall externo:

```bash
# Permitir acceso desde red específica
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" port protocol="tcp" port="9090" accept'
sudo firewall-cmd --reload
```

### Configurar Nginx como Proxy Reverso (Recomendado para Producción)

```nginx
server {
    listen 80;
    server_name diaken.yourcompany.com;

    location / {
        proxy_pass http://127.0.0.1:9090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📞 Soporte

- **GitHub Issues:** https://github.com/htheran/diaken-free/issues
- **Documentación:** https://github.com/htheran/diaken-free
- **Email:** (agregar si aplica)

---

## 📄 Licencia

Ver archivo `LICENSE` en el repositorio.

---

**¡Gracias por usar Diaken!** 🎉
