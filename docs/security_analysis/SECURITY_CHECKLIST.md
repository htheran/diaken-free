# ✅ Security Implementation Checklist - Diaken Project

## 🔴 CRÍTICO - Implementar INMEDIATAMENTE

### [ ] 1. Migrar SECRET_KEY a Variables de Entorno
```bash
# Generar nueva SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Agregar a .env
echo "DJANGO_SECRET_KEY=nueva-clave-generada" >> .env

# Actualizar settings.py
# SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
```
**Prioridad:** 🔴 CRÍTICA  
**Tiempo estimado:** 15 minutos  
**Impacto:** Protege sesiones y tokens

---

### [ ] 2. Configurar ALLOWED_HOSTS Correctamente
```python
# En settings.py reemplazar:
# ALLOWED_HOSTS = ['*']
# Por:
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')]
```
**Prioridad:** 🔴 CRÍTICA  
**Tiempo estimado:** 10 minutos  
**Impacto:** Previene Host Header injection

---

### [ ] 3. Encriptar Credenciales en Base de Datos
```bash
# Generar clave de encriptación
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'

# Agregar a .env
echo "ENCRYPTION_KEY=clave-generada" >> .env

# Crear archivo de migración para encriptar credenciales existentes
python manage.py makemigrations
python manage.py migrate
```
**Prioridad:** 🔴 CRÍTICA  
**Tiempo estimado:** 2-4 horas  
**Impacto:** Protege credenciales de infraestructura  
**Archivos:** `settings/models.py`

---

### [ ] 4. Sanitizar Inputs en subprocess.run()
**Archivos a modificar:**
- [ ] `deploy/govc_helper.py` (líneas 43-51, 109-119)
- [ ] `deploy/views.py` (líneas 405, 498, 588, 1002)
- [ ] `deploy/views_playbook.py` (líneas 324, 372)
- [ ] `deploy/views_windows.py` (línea 335)
- [ ] `scheduler/management/commands/run_scheduled_tasks.py`

**Prioridad:** 🔴 CRÍTICA  
**Tiempo estimado:** 4-6 horas  
**Impacto:** Previene inyección de comandos

---

### [ ] 5. Remover @csrf_exempt
```python
# En login/views.py
# Remover línea 34: from django.views.decorators.csrf import csrf_exempt
# Remover línea 36: @csrf_exempt
```
**Prioridad:** 🔴 ALTA  
**Tiempo estimado:** 15 minutos  
**Impacto:** Protege contra CSRF attacks

---

## 🟠 ALTA PRIORIDAD - Semanas 2-3

### [ ] 6. Implementar Rate Limiting
```bash
pip install django-ratelimit
```
**Archivos:** `login/views.py`, `deploy/views.py`  
**Prioridad:** 🟠 ALTA  
**Tiempo estimado:** 2 horas

---

### [ ] 7. Migrar a PostgreSQL
```bash
pip install psycopg2-binary
createdb diaken
python manage.py dumpdata > backup.json
# Cambiar configuración
python manage.py migrate
python manage.py loaddata backup.json
```
**Prioridad:** 🟠 ALTA  
**Tiempo estimado:** 4 horas  
**Impacto:** Mejora concurrencia y rendimiento

---

### [ ] 8. Configurar HTTPS Obligatorio
```python
# En settings_production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```
**Prioridad:** 🟠 ALTA  
**Tiempo estimado:** 1 hora + configuración certificados

---

### [ ] 9. Validación de Archivos Subidos
**Archivos:** `settings/models.py`, `playbooks/models.py`  
**Prioridad:** 🟠 ALTA  
**Tiempo estimado:** 2-3 horas

---

### [ ] 10. Implementar Auditoría de Acciones
**Prioridad:** 🟠 ALTA  
**Tiempo estimado:** 6-8 horas  
**Crear modelo AuditLog**

---

## 🟡 MEDIA PRIORIDAD - Mes 2

### [ ] 11. Sanitizar Logs de Datos Sensibles
**Prioridad:** 🟡 MEDIA  
**Tiempo estimado:** 3 horas

---

### [ ] 12. Implementar 2FA
```bash
pip install django-otp qrcode
```
**Prioridad:** 🟡 MEDIA  
**Tiempo estimado:** 8-10 horas

---

### [ ] 13. Control de Acceso Basado en Roles (RBAC)
**Prioridad:** 🟡 MEDIA  
**Tiempo estimado:** 10-12 horas

---

### [ ] 14. Escapar Variables en mark_safe()
**Archivos:** `deploy/views.py`  
**Prioridad:** 🟡 MEDIA  
**Tiempo estimado:** 1 hora

---

### [ ] 15. Headers de Seguridad
```python
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```
**Prioridad:** 🟡 MEDIA  
**Tiempo estimado:** 30 minutos

---

## 🟢 BAJA PRIORIDAD - Mejoras Continuas

### [ ] 16. Dockerización
**Tiempo estimado:** 6-8 horas

---

### [ ] 17. Tests Automatizados
**Tiempo estimado:** Continuo

---

### [ ] 18. Implementar Caché con Redis
**Tiempo estimado:** 4 horas

---

### [ ] 19. Optimizar Queries de BD
**Tiempo estimado:** Continuo

---

### [ ] 20. API Versionada
**Tiempo estimado:** 12+ horas

---

## 📊 Progreso Total

**Completado:** 0/20 (0%)

- 🔴 Crítico: 0/5
- 🟠 Alta: 0/5
- 🟡 Media: 0/5
- 🟢 Baja: 0/5

---

## 🛠️ Comandos Útiles

### Verificar Seguridad
```bash
python manage.py check --deploy
```

### Auditar Dependencias
```bash
pip install safety
safety check
```

### Generar Claves
```bash
# SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# ENCRYPTION_KEY
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

### Backup de Base de Datos
```bash
python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

---

## 📝 Notas

- Realizar backup antes de cada cambio crítico
- Probar en entorno de desarrollo primero
- Documentar cambios en CHANGELOG
- Notificar al equipo antes de implementar cambios que afecten sesiones
