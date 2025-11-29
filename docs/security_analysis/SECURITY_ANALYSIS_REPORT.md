# 🔒 Análisis de Seguridad y Mejoras - Diaken Project

**Fecha:** 2025-10-16  
**Proyecto:** Diaken - Automated VM Deployment & Infrastructure Management  
**Django:** 5.2.6 | **Python:** 3.12

---

## 📋 RESUMEN EJECUTIVO

Análisis exhaustivo de seguridad identificando vulnerabilidades críticas, riesgos y oportunidades de mejora.

**Puntuación de Seguridad:** ⚠️ 6.5/10 - **ATENCIÓN REQUERIDA**

---

## 🚨 VULNERABILIDADES CRÍTICAS

### 1. SECRET_KEY Hardcoded (🔴 CRÍTICA)
**Archivo:** `/diaken/settings.py:26`

**Problema:**
```python
SECRET_KEY = 'django-insecure-=n6@0_5-87_)fy5=8ph$y(=vr*w6*9ig-$%7)hxk)nr405)$b^'
```
- Clave hardcoded en código fuente
- Compromete sesiones, CSRF tokens y firmas criptográficas

**Solución:**
```python
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY not set")
```

**Acción:** Generar nueva clave, almacenar en variable de entorno, rotar inmediatamente.

---

### 2. ALLOWED_HOSTS = ['*'] (🔴 CRÍTICA)
**Archivo:** `/diaken/settings.py:33`

**Problema:**
- Permite Host Header injection
- Cache poisoning y password reset poisoning

**Solución:**
```python
ALLOWED_HOSTS_STR = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_STR.split(',') if h.strip()] or ['localhost']
```

---

### 3. Inyección de Comandos en subprocess (🔴 CRÍTICA)
**Archivos:** `deploy/govc_helper.py`, `deploy/views.py`, `scheduler/management/commands/run_scheduled_tasks.py`

**Problema:**
```python
govc_cmd = ['govc', 'vm.network.change', '-vm', vm_name, '-net', network_name]
subprocess.run(govc_cmd, ...)  # ⚠️ Sin sanitización
```
- Parámetros de usuario sin validar
- Potencial ejecución arbitraria de comandos

**Solución:**
```python
import re

def sanitize_vm_name(vm_name):
    if not re.match(r'^[a-zA-Z0-9_-]+$', vm_name):
        raise ValueError(f"Invalid VM name: {vm_name}")
    return vm_name

vm_name = sanitize_vm_name(vm_name)
```

**Archivos a corregir:**
- `deploy/govc_helper.py` (líneas 43-51, 109-119)
- `deploy/views.py` (líneas 405, 498, 588, 1002)
- `deploy/views_playbook.py` (líneas 324, 372)
- `deploy/views_windows.py` (línea 335)

---

### 4. Credenciales en Texto Plano (🔴 CRÍTICA)
**Archivo:** `/settings/models.py`

**Problema:**
```python
class VCenterCredential(models.Model):
    password = models.CharField(max_length=255)  # ⚠️ Sin encriptar

class WindowsCredential(models.Model):
    password = models.CharField(max_length=255)  # ⚠️ Sin encriptar
```
- Contraseñas de infraestructura sin encriptar
- Database SQLite de 22MB expuesto

**Solución:**
```python
from cryptography.fernet import Fernet
import base64

class EncryptedCredentialMixin:
    @staticmethod
    def get_cipher():
        key = settings.ENCRYPTION_KEY.encode()
        return Fernet(base64.urlsafe_b64encode(key.ljust(32)[:32]))
    
    def set_encrypted_password(self, password):
        if password:
            cipher = self.get_cipher()
            self.password = cipher.encrypt(password.encode()).decode()
    
    def get_decrypted_password(self):
        if self.password:
            cipher = self.get_cipher()
            return cipher.decrypt(self.password.encode()).decode()
```

**Requerido:** Variable de entorno `ENCRYPTION_KEY`

---

### 5. Bypass CSRF Protection (🔴 ALTA)
**Archivo:** `/login/views.py:34-36`

**Problema:**
```python
@csrf_exempt
def set_language(request):  # ⚠️ Vista POST sin CSRF
```

**Solución:** Remover `@csrf_exempt` y usar protección CSRF normal.

---

### 6. SQLite en Producción (🟡 MEDIA)
**Archivos:** `diaken/settings.py`, `diaken/settings_production.py`

**Problema:**
- SQLite no soporta concurrencia
- 22MB database file en repositorio

**Solución:** Migrar a PostgreSQL
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'diaken'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

---

## ⚠️ VULNERABILIDADES MEDIA

### 7. XSS via mark_safe() (🟡 MEDIA)
**Archivo:** `/deploy/views.py`

**Problema:**
```python
messages.error(request, mark_safe(f'<b>{hostname}</b>'))  # ⚠️ Sin escapar
```

**Solución:**
```python
from django.utils.html import escape
messages.error(request, mark_safe(f'<b>{escape(hostname)}</b>'))
```

---

### 8. Sin Rate Limiting (🟡 MEDIA)
**Archivo:** `/login/views.py`

**Solución:**
```python
pip install django-ratelimit

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    ...
```

---

### 9. Validación de Archivos Insuficiente (🟡 MEDIA)

**Solución:**
```python
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    if ext.lower() not in ['.pem', '.key', '.pub']:
        raise ValidationError(f'Invalid extension: {ext}')

def validate_file_size(value):
    if value.size > 1024 * 1024:  # 1MB
        raise ValidationError('File too large')
```

---

### 10. Logs con Datos Sensibles (🟡 MEDIA)

**Solución:**
```python
class SensitiveDataFilter(logging.Filter):
    PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\']+)', 'password=***'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\']+)', 'token=***'),
    ]
    
    def filter(self, record):
        import re
        msg = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.I)
        record.msg = msg
        return True
```

---

## 🔧 MEJORAS RECOMENDADAS

### 11. Autenticación de Dos Factores (2FA)
```bash
pip install django-otp qrcode
```

### 12. Auditoría de Acciones
```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    changes = models.JSONField(default=dict)
```

### 13. Control de Acceso (RBAC)
```python
groups = {
    'Admin': ['add', 'change', 'delete', 'view'],
    'Operator': ['add', 'view'],
    'Viewer': ['view'],
}
```

### 14. HTTPS Obligatorio
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### 15. Headers de Seguridad
```python
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

### 16. Validación de Playbooks
```python
def validate_playbook_content(content):
    data = yaml.safe_load(content)
    dangerous_patterns = ['rm -rf', 'dd if=', 'mkfs']
    content_lower = content.lower()
    for pattern in dangerous_patterns:
        if pattern in content_lower:
            raise ValueError(f"Dangerous pattern: {pattern}")
```

---

## 📊 MEJORAS DE ARQUITECTURA

### 17. Separar Lógica de Negocio
```python
# services/vm_deployment.py
class VMDeploymentService:
    def __init__(self, vcenter_credential):
        self.vcenter = vcenter_credential
    
    def deploy_vm(self, config):
        # Lógica centralizada
        pass
```

### 18. Implementar Tests
```python
class SecurityTestCase(TestCase):
    def test_login_required(self):
        response = self.client.get('/deploy/')
        self.assertEqual(response.status_code, 302)
    
    def test_csrf_protection(self):
        response = self.client.post('/deploy/', {})
        self.assertEqual(response.status_code, 403)
```

### 19. Dockerización
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN useradd -m diaken && chown -R diaken:diaken /app
USER diaken
EXPOSE 8000
CMD ["gunicorn", "diaken.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 20. Variables de Entorno
```bash
# .env.example
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=diaken
DB_USER=diaken
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
ENCRYPTION_KEY=
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### Fase 1: CRÍTICO (Semana 1)
1. ✅ SECRET_KEY a variable de entorno
2. ✅ ALLOWED_HOSTS configuración correcta
3. ✅ Encriptar credenciales
4. ✅ Sanitizar subprocess inputs
5. ✅ Remover @csrf_exempt

### Fase 2: ALTA (Semanas 2-3)
6. ✅ Rate Limiting
7. ✅ Validación de archivos
8. ✅ HTTPS obligatorio
9. ✅ Migrar a PostgreSQL
10. ✅ Auditoría de acciones

### Fase 3: MEDIA (Mes 2)
11. ✅ 2FA
12. ✅ Tests automatizados
13. ✅ RBAC
14. ✅ Dockerización
15. ✅ Headers de seguridad

### Fase 4: CONTINUA (Mes 3+)
16. ✅ Caché con Redis
17. ✅ Optimización de queries
18. ✅ API versionada
19. ✅ Monitoreo y alertas
20. ✅ Documentación completa

---

## 📈 RECURSOS ADICIONALES

### Dependencias Adicionales Recomendadas
```txt
# Seguridad
django-ratelimit==4.1.0
django-otp==1.3.0
qrcode==7.4.2
cryptography==42.0.5
django-csp==3.8

# Base de datos
psycopg2-binary==2.9.9

# Producción
gunicorn==21.2.0
django-redis==5.4.0
redis==5.0.1

# Monitoreo
sentry-sdk==1.40.0
```

### Comandos Útiles
```bash
# Generar SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Generar ENCRYPTION_KEY
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'

# Verificar configuración de seguridad
python manage.py check --deploy

# Auditar dependencias
pip install safety
safety check
```

---

## 📞 CONTACTO Y SOPORTE

Para implementar estas mejoras o consultas:
- Documentación Django Security: https://docs.djangoproject.com/en/5.2/topics/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

---

**Fin del Reporte**
