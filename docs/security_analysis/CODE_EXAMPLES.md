# 💻 Ejemplos de Código Corregido - Diaken Project

Este documento muestra ejemplos específicos de código vulnerable y su corrección.

---

## 🔴 1. Command Injection en govc_helper.py

### ❌ CÓDIGO VULNERABLE (Actual)

```python
# deploy/govc_helper.py - VULNERABLE
def change_vm_network_govc(vcenter_host, vcenter_user, vcenter_password, vm_name, network_name):
    govc_cmd = [
        'govc', 'vm.network.change',
        '-vm', vm_name,              # ⚠️ Sin sanitización
        '-net', network_name,        # ⚠️ Sin sanitización
        'ethernet-0'
    ]
    
    result = subprocess.run(
        govc_cmd,
        env=govc_env,
        capture_output=True,
        text=True,
        timeout=30
    )
```

**Riesgo:** Si `vm_name` contiene `; rm -rf /` se ejecutará el comando malicioso.

### ✅ CÓDIGO CORREGIDO

```python
# deploy/govc_helper.py - SEGURO
from security_fixes.sanitization_helpers import InputSanitizer
import logging

logger = logging.getLogger('deploy.govc_helper')

def change_vm_network_govc(vcenter_host, vcenter_user, vcenter_password, vm_name, network_name):
    """
    Change VM network using govc CLI
    
    Args:
        vcenter_host: vCenter hostname or IP
        vcenter_user: vCenter username
        vcenter_password: vCenter password
        vm_name: Name of the VM (will be sanitized)
        network_name: Name of the target network (will be sanitized)
        
    Returns:
        tuple: (success: bool, message: str)
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Sanitizar inputs ANTES de usar
    try:
        vm_name = InputSanitizer.sanitize_vm_name(vm_name)
        network_name = InputSanitizer.sanitize_network_name(network_name)
    except ValueError as e:
        logger.error(f"Input validation failed: {e}")
        return False, f"Invalid input: {e}"
    
    logger.debug(f'GOVC: VM: {vm_name}, Network: {network_name}')
    
    # Configurar variables de entorno
    govc_env = os.environ.copy()
    govc_env['GOVC_URL'] = vcenter_host
    govc_env['GOVC_USERNAME'] = vcenter_user
    govc_env['GOVC_PASSWORD'] = vcenter_password
    govc_env['GOVC_INSECURE'] = 'true'
    
    try:
        # Construir comando con inputs sanitizados
        govc_cmd = [
            'govc', 'vm.network.change',
            '-vm', vm_name,
            '-net', network_name,
            'ethernet-0'
        ]
        
        result = subprocess.run(
            govc_cmd,
            env=govc_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f'Network changed successfully: {network_name}')
            return True, f'Network changed to: {network_name}'
        else:
            logger.error(f'govc error: {result.stderr}')
            return False, f'Error: {result.stderr}'
            
    except subprocess.TimeoutExpired:
        logger.error('govc command timeout')
        return False, 'Timeout (>30s)'
    except Exception as e:
        logger.error(f'Exception: {e}')
        return False, f'Exception: {str(e)}'
```

---

## 🔴 2. Credenciales en Texto Plano

### ❌ CÓDIGO VULNERABLE (Actual)

```python
# settings/models.py - VULNERABLE
class VCenterCredential(models.Model):
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255)
    user = models.CharField(max_length=100)
    password = models.CharField(max_length=255)  # ⚠️ Texto plano
    
    def __str__(self):
        return f"{self.name} ({self.host})"
```

**Riesgo:** Cualquiera con acceso a la base de datos puede leer las contraseñas.

### ✅ CÓDIGO CORREGIDO

```python
# settings/models.py - SEGURO
from security_fixes.credential_encryption import EncryptedCredentialMixin
from django.db import models
import logging

logger = logging.getLogger(__name__)

class VCenterCredential(EncryptedCredentialMixin, models.Model):
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255)
    user = models.CharField(max_length=100)
    password = models.TextField()  # Almacena encriptado
    ssl_verify = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        """Override save to encrypt password"""
        if not self.pk:  # Nueva credencial
            # Guardar temporalmente el password plano
            plain_password = self.password
            
            # Primero guardar el registro (para obtener PK)
            super().save(*args, **kwargs)
            
            # Encriptar y actualizar
            self.set_encrypted_password(plain_password)
            super().save(update_fields=['password'])
            
            logger.info(f"Created encrypted credential: {self.name}")
        else:
            # Actualización - verificar si cambió el password
            if self.pk:
                old = VCenterCredential.objects.get(pk=self.pk)
                if old.password != self.password:
                    # Password cambió - encriptar
                    plain_password = self.password
                    super().save(*args, **kwargs)
                    self.set_encrypted_password(plain_password)
                    super().save(update_fields=['password'])
                    logger.info(f"Updated encrypted credential: {self.name}")
                else:
                    super().save(*args, **kwargs)
            else:
                super().save(*args, **kwargs)
    
    def get_password(self):
        """Get decrypted password"""
        return self.get_decrypted_password()
    
    def __str__(self):
        return f"{self.name} ({self.host})"
    
    class Meta:
        verbose_name = "vCenter Credential"
        verbose_name_plural = "vCenter Credentials"
        ordering = ['name']
```

**Uso en código:**
```python
# En vez de: vcenter_password = cred.password
# Usar:
vcenter_password = cred.get_password()
```

---

## 🔴 3. CSRF Bypass en Login

### ❌ CÓDIGO VULNERABLE (Actual)

```python
# login/views.py - VULNERABLE
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # ⚠️ Deshabilita protección CSRF
def set_language(request):
    if request.method == 'POST':
        lang = request.POST.get('language', 'en')
        if lang in ['en', 'es']:
            request.session['django_language'] = lang
            translation.activate(lang)
    return redirect(request.META.get('HTTP_REFERER', '/'))
```

**Riesgo:** Atacante puede cambiar idioma de sesiones de otros usuarios.

### ✅ CÓDIGO CORREGIDO

```python
# login/views.py - SEGURO
from django.utils import translation
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])  # Solo POST
def set_language(request):
    """
    Set user language preference
    
    CSRF protection is enabled (no @csrf_exempt)
    """
    if request.method == 'POST':
        lang = request.POST.get('language', 'en')
        
        # Validar idioma
        if lang not in ['en', 'es']:
            logger.warning(f"Invalid language attempt: {lang} from {request.user}")
            lang = 'en'
        
        # Cambiar idioma de sesión
        request.session['django_language'] = lang
        translation.activate(lang)
        
        logger.info(f"Language changed to {lang} for user {request.user}")
    
    # Redirect seguro
    referer = request.META.get('HTTP_REFERER', '/')
    # Validar que el referer es de nuestro dominio
    from django.conf import settings
    from urllib.parse import urlparse
    
    parsed = urlparse(referer)
    if parsed.netloc and parsed.netloc not in settings.ALLOWED_HOSTS:
        referer = '/'
    
    return redirect(referer)
```

**Template actualizado:**
```html
<!-- Agregar CSRF token en el formulario -->
<form method="post" action="{% url 'set_language' %}">
    {% csrf_token %}
    <select name="language" onchange="this.form.submit()">
        <option value="en">English</option>
        <option value="es">Español</option>
    </select>
</form>
```

---

## 🔴 4. XSS via mark_safe()

### ❌ CÓDIGO VULNERABLE (Actual)

```python
# deploy/views.py - VULNERABLE
from django.utils.safestring import mark_safe

messages.error(request, mark_safe(
    f'<b>❌ Hostname already exists!</b><br>'
    f'The hostname <b>{hostname}</b> is already registered.'  # ⚠️ Sin escapar
))
```

**Riesgo:** Si hostname contiene `<script>alert('XSS')</script>` se ejecutará.

### ✅ CÓDIGO CORREGIDO

```python
# deploy/views.py - SEGURO
from django.utils.safestring import mark_safe
from django.utils.html import escape

messages.error(request, mark_safe(
    f'<b>❌ Hostname already exists!</b><br>'
    f'The hostname <b>{escape(hostname)}</b> is already registered.'  # ✅ Escapado
))

# O mejor aún, usar formato sin HTML:
messages.error(request, 
    f'Hostname already exists: {hostname}. Please choose a different name.'
)
```

---

## 🔴 5. Deploy View - Múltiples Mejoras

### ❌ CÓDIGO VULNERABLE (Extracto)

```python
# deploy/views.py - VULNERABLE
def deploy_vm(request):
    if form.is_valid():
        hostname = form.cleaned_data['hostname']  # ⚠️ Sin validar
        ip = form.cleaned_data['ip']  # ⚠️ Sin validar
        
        # ... código ...
        
        cmd = [
            'ansible-playbook', playbook,
            '-i', f'{ip},',  # ⚠️ IP sin validar
            '--extra-vars', f'hostname={hostname}'  # ⚠️ Inyección posible
        ]
        
        subprocess.run(cmd, ...)  # ⚠️ Peligroso
```

### ✅ CÓDIGO CORREGIDO

```python
# deploy/views.py - SEGURO
from security_fixes.sanitization_helpers import InputSanitizer
from django.utils.html import escape
import json
import logging

logger = logging.getLogger('deploy.views')

@login_required
def deploy_vm(request):
    """Deploy VM with security validations"""
    
    if request.method == 'POST':
        form = DeployVMForm(request.POST)
        
        if form.is_valid():
            try:
                # Sanitizar TODOS los inputs
                hostname = InputSanitizer.sanitize_hostname(
                    form.cleaned_data['hostname']
                )
                ip = InputSanitizer.sanitize_ip_address(
                    form.cleaned_data['ip']
                )
                template = InputSanitizer.sanitize_vm_name(
                    form.cleaned_data['template']
                )
                datacenter = InputSanitizer.sanitize_datacenter_name(
                    form.cleaned_data['datacenter']
                )
                network = InputSanitizer.sanitize_network_name(
                    form.cleaned_data['network']
                )
                
                logger.info(f"Deployment request by {request.user.username}: "
                           f"hostname={hostname}, ip={ip}")
                
                # Validar que hostname e IP no existen
                if Host.objects.filter(name=hostname, active=True).exists():
                    messages.error(request, 
                        f'Hostname {escape(hostname)} already exists.')
                    return redirect('deploy:deploy_vm')
                
                if Host.objects.filter(ip=ip, active=True).exists():
                    messages.error(request, 
                        f'IP {escape(ip)} already assigned.')
                    return redirect('deploy:deploy_vm')
                
                # Construir comando Ansible de forma segura
                # Usar JSON para extra-vars (previene inyección)
                extra_vars = {
                    'hostname': hostname,
                    'ip_address': ip,
                    'network': network,
                }
                
                cmd = [
                    'ansible-playbook',
                    playbook_path,
                    '-i', f'{ip},',
                    '--extra-vars', json.dumps(extra_vars),  # ✅ Seguro
                    '--timeout', '600'
                ]
                
                # Ejecutar con timeout y logging
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,
                    check=False  # No raise exception en error
                )
                
                # Log del resultado
                if result.returncode == 0:
                    logger.info(f"Deployment successful: {hostname}")
                    messages.success(request, 
                        f'VM {escape(hostname)} deployed successfully!')
                else:
                    logger.error(f"Deployment failed: {hostname}, "
                               f"returncode={result.returncode}")
                    messages.error(request, 
                        f'Deployment failed. Check logs.')
                
                return redirect('history:deployment_list')
                
            except ValueError as e:
                # Error de validación
                logger.warning(f"Validation error: {e}")
                messages.error(request, f'Invalid input: {e}')
                return redirect('deploy:deploy_vm')
            
            except subprocess.TimeoutExpired:
                logger.error(f"Deployment timeout: {hostname}")
                messages.error(request, 'Deployment timeout (>10 min)')
                return redirect('deploy:deploy_vm')
            
            except Exception as e:
                logger.error(f"Deployment exception: {e}", exc_info=True)
                messages.error(request, 'Deployment error. Contact admin.')
                return redirect('deploy:deploy_vm')
        else:
            messages.error(request, 'Form validation failed.')
    
    else:
        form = DeployVMForm()
    
    return render(request, 'deploy/deploy_vm_form.html', {'form': form})
```

---

## 🟡 6. Settings.py - Configuración Segura

### ❌ CONFIGURACIÓN VULNERABLE (Actual)

```python
# diaken/settings.py - VULNERABLE
SECRET_KEY = 'django-insecure-=n6@0_5-87_)fy5=8ph$y(=vr*w6*9ig-$%7)hxk)nr405)$b^'
DEBUG = False
ALLOWED_HOSTS = ['*']  # ⚠️ Acepta cualquier host
```

### ✅ CONFIGURACIÓN SEGURA

```python
# diaken/settings.py - SEGURO
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: Load from environment variables
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY environment variable is required. "
        "Generate one with: python -c 'from django.core.management.utils "
        "import get_random_secret_key; print(get_random_secret_key())'"
    )

# Debug mode
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# Allowed hosts from environment
ALLOWED_HOSTS_STR = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_STR:
    ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_STR.split(',') if h.strip()]
else:
    if DEBUG:
        ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
    else:
        raise ValueError("DJANGO_ALLOWED_HOSTS must be set in production")

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS_STR = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if CSRF_TRUSTED_ORIGINS_STR:
    CSRF_TRUSTED_ORIGINS = [
        o.strip() for o in CSRF_TRUSTED_ORIGINS_STR.split(',') if o.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = []

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# CSRF security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

---

## 📊 Resumen de Cambios

| Vulnerabilidad | Archivo | Solución | Prioridad |
|---|---|---|---|
| Command Injection | `govc_helper.py` | InputSanitizer | 🔴 CRÍTICA |
| Credenciales Texto Plano | `models.py` | EncryptedCredentialMixin | 🔴 CRÍTICA |
| CSRF Bypass | `login/views.py` | Remover @csrf_exempt | 🔴 ALTA |
| XSS | `deploy/views.py` | escape() en mark_safe() | 🟡 MEDIA |
| SECRET_KEY Hardcoded | `settings.py` | Variable de entorno | 🔴 CRÍTICA |
| ALLOWED_HOSTS ['*'] | `settings.py` | Configuración específica | 🔴 CRÍTICA |

---

## 🚀 Testing

### Unit Tests
```python
# tests/test_security.py
from django.test import TestCase
from security_fixes.sanitization_helpers import InputSanitizer

class InputSanitizerTest(TestCase):
    def test_sanitize_vm_name_valid(self):
        """Test valid VM name"""
        result = InputSanitizer.sanitize_vm_name("test-vm-01")
        self.assertEqual(result, "test-vm-01")
    
    def test_sanitize_vm_name_injection(self):
        """Test command injection prevention"""
        with self.assertRaises(ValueError):
            InputSanitizer.sanitize_vm_name("test; rm -rf /")
    
    def test_sanitize_ip_valid(self):
        """Test valid IP address"""
        result = InputSanitizer.sanitize_ip_address("192.168.1.100")
        self.assertEqual(result, "192.168.1.100")
    
    def test_sanitize_ip_invalid(self):
        """Test invalid IP address"""
        with self.assertRaises(ValueError):
            InputSanitizer.sanitize_ip_address("999.999.999.999")
```

---

**Fin de Ejemplos**
