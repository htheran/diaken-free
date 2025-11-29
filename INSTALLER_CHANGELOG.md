# 📝 Changelog del Instalador Diaken

Historial de mejoras y actualizaciones del instalador automático.

---

## [v2.0] - 2025-11-29

### 🎉 Versión Completamente Automatizada

#### ✨ Nuevas Características

##### 1. **Instalación Desatendida**
- Soporte para variables de entorno
- Modo completamente automático sin intervención
- Valores por defecto inteligentes

```bash
# Instalación en un solo comando
curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken.sh | \
  sudo DJANGO_SUPERUSER_PASSWORD=YourPassword bash
```

##### 2. **Servicios Automáticos**
- ✅ Redis instalado y configurado automáticamente
- ✅ Celery Worker con systemd
- ✅ Auto-restart en caso de fallo
- ✅ Logs centralizados

##### 3. **Variables Dinámicas**
- Detección automática de usuario (sin hardcodear)
- Rutas relativas y portables
- Funciona en cualquier servidor sin modificaciones

##### 4. **PATH Completo en Celery**
- Acceso a todos los comandos del sistema
- SSH, SCP, Ansible disponibles
- Soluciona error: "No such file or directory: b'ssh'"

##### 5. **Dependencias Completas**
- Redis agregado
- openssh-clients agregado
- Todas las herramientas necesarias incluidas

#### 🔧 Mejoras

- Servicio Diaken se crea automáticamente (sin preguntar)
- Superuser con valores por defecto (username: admin)
- Mensajes de progreso mejorados
- Verificación de servicios post-instalación
- Documentación completa incluida

#### 🐛 Correcciones

- Corregido PATH limitado en Celery
- Corregido permisos de llaves SSH (auto-corrección)
- Corregido servicio Celery (PIDFile en lugar de ExecStop)
- Eliminadas preguntas innecesarias

#### 📚 Documentación Nueva

- `INSTALL_UNATTENDED.md` - Guía de instalación desatendida
- `TROUBLESHOOTING_SSH.md` - Troubleshooting de SSH
- `DEPLOY_ROUTES_VALIDATION.md` - Validación de rutas
- `INSTALLER_CHANGELOG.md` - Este archivo

---

## [v1.0] - 2025-11-28

### 🎯 Versión Inicial

#### Características

- Instalación básica de Diaken
- Configuración de Python 3.12
- Instalación de dependencias
- Creación de superuser (interactivo)
- Configuración de firewall
- Servicio systemd opcional

#### Limitaciones

- Redis no incluido (instalación manual)
- Celery no configurado
- Usuarios hardcodeados
- Instalación completamente interactiva
- Sin soporte para desatendido

---

## 🔄 Migración de v1.0 a v2.0

Si ya tienes Diaken instalado con v1.0, actualiza así:

### Paso 1: Instalar Redis

```bash
sudo dnf install redis -y
sudo systemctl start redis
sudo systemctl enable redis
```

### Paso 2: Configurar Celery

```bash
# Crear directorios
sudo mkdir -p /var/log/diaken/celery /var/run/diaken/celery
sudo chown -R $(whoami):$(whoami) /var/log/diaken /var/run/diaken

# Crear servicio
sudo tee /etc/systemd/system/celery.service > /dev/null << 'EOF'
[Unit]
Description=Celery Service for Diaken
After=network.target redis.service

[Service]
Type=forking
User=YOUR_USER
Group=YOUR_USER
WorkingDirectory=/opt/diaken
Environment="PATH=/opt/diaken/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/diaken/venv/bin/celery -A diaken worker --loglevel=info --detach --logfile=/var/log/diaken/celery/worker.log --pidfile=/var/run/diaken/celery/worker.pid
PIDFile=/var/run/diaken/celery/worker.pid
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

# Reemplazar YOUR_USER con tu usuario
sudo sed -i "s/YOUR_USER/$(whoami)/g" /etc/systemd/system/celery.service

# Iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery
```

### Paso 3: Instalar openssh-clients

```bash
sudo dnf install openssh-clients -y
```

### Paso 4: Verificar

```bash
sudo systemctl status redis celery
```

---

## 📊 Comparación de Versiones

| Característica | v1.0 | v2.0 |
|----------------|------|------|
| **Instalación** | Interactiva | Desatendida |
| **Redis** | ❌ Manual | ✅ Automático |
| **Celery** | ❌ Manual | ✅ Automático |
| **SSH Client** | ❌ No incluido | ✅ Incluido |
| **Variables** | ❌ Hardcodeadas | ✅ Dinámicas |
| **PATH Celery** | ❌ Limitado | ✅ Completo |
| **Servicios** | ❌ Opcionales | ✅ Automáticos |
| **Documentación** | ⚠️ Básica | ✅ Completa |
| **Portabilidad** | ⚠️ Limitada | ✅ Total |

---

## 🚀 Próximas Mejoras (v3.0)

### Planificadas

- [ ] Soporte para PostgreSQL (alternativa a SQLite)
- [ ] Configuración de Nginx como proxy reverso
- [ ] Certificados SSL/TLS automáticos (Let's Encrypt)
- [ ] Soporte para Docker/Docker Compose
- [ ] Backup automático de base de datos
- [ ] Monitoreo con Prometheus/Grafana
- [ ] Alta disponibilidad (múltiples workers)
- [ ] Soporte para Debian/Ubuntu (además de RedHat)

### En Consideración

- [ ] Instalación en Kubernetes
- [ ] Integración con LDAP/Active Directory
- [ ] Multi-tenancy
- [ ] API REST completa
- [ ] CLI para administración

---

## 🐛 Problemas Conocidos

### v2.0

Ninguno reportado hasta el momento.

### v1.0

- ❌ Redis no instalado (requiere instalación manual)
- ❌ Celery no configurado (deployments fallan)
- ❌ PATH limitado (error: ssh not found)
- ❌ Usuarios hardcodeados (no portable)

**Todos resueltos en v2.0**

---

## 📞 Soporte

- **GitHub Issues:** https://github.com/htheran/diaken-free/issues
- **Documentación:** https://github.com/htheran/diaken-free
- **Email:** (agregar si aplica)

---

## 📄 Licencia

Ver archivo `LICENSE` en el repositorio.

---

**Última actualización:** 2025-11-29  
**Versión actual:** v2.0  
**Mantenedor:** htheran
