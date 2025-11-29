# 🔐 Security Fixes - Diaken Project

Este directorio contiene utilidades y scripts de ayuda para implementar las correcciones de seguridad identificadas en el análisis.

## 📁 Archivos

### 1. `sanitization_helpers.py`
Funciones de sanitización de inputs para prevenir inyección de comandos.

**Uso:**
```python
from security_fixes.sanitization_helpers import InputSanitizer

# Sanitizar VM name
try:
    safe_vm_name = InputSanitizer.sanitize_vm_name(user_input)
except ValueError as e:
    # Manejar error de validación
    print(f"Invalid input: {e}")

# Sanitizar IP address
safe_ip = InputSanitizer.sanitize_ip_address(ip_input)

# Sanitizar hostname
safe_hostname = InputSanitizer.sanitize_hostname(hostname_input)
```

### 2. `credential_encryption.py`
Sistema de encriptación para credenciales en base de datos.

**Generar clave de encriptación:**
```bash
cd /opt/www/app/diaken-pdn
python security_fixes/credential_encryption.py generate-key
```

**Probar encriptación:**
```bash
python security_fixes/credential_encryption.py test
```

**Migrar credenciales existentes:**
```bash
# Asegurar que ENCRYPTION_KEY está en .env
python security_fixes/credential_encryption.py migrate
```

## 🚀 Implementación Rápida

### Paso 1: Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Generar SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Generar ENCRYPTION_KEY
python security_fixes/credential_encryption.py generate-key

# Agregar a .env
cat >> .env << 'EOF'
DJANGO_SECRET_KEY=<tu-secret-key-generada>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
ENCRYPTION_KEY=<tu-encryption-key-generada>
EOF
```

### Paso 2: Actualizar settings.py

```python
# En diaken/settings.py
import os

# SECRET_KEY desde variable de entorno
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable not set")

# ALLOWED_HOSTS desde variable de entorno
ALLOWED_HOSTS_STR = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_STR:
    ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_STR.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

### Paso 3: Actualizar govc_helper.py

```python
# En deploy/govc_helper.py
from security_fixes.sanitization_helpers import InputSanitizer

def change_vm_network_govc(vcenter_host, vcenter_user, vcenter_password, vm_name, network_name):
    # Sanitizar inputs
    vm_name = InputSanitizer.sanitize_vm_name(vm_name)
    network_name = InputSanitizer.sanitize_network_name(network_name)
    
    # Resto del código...
    govc_cmd = [
        'govc', 'vm.network.change',
        '-vm', vm_name,
        '-net', network_name,
        'ethernet-0'
    ]
```

### Paso 4: Encriptar Credenciales

```python
# En settings/models.py
from security_fixes.credential_encryption import EncryptedCredentialMixin

class VCenterCredential(EncryptedCredentialMixin, models.Model):
    host = models.CharField(max_length=255)
    user = models.CharField(max_length=100)
    password = models.TextField()  # Será encriptado
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Solo en creación
            plain_password = self.password
            super().save(*args, **kwargs)
            self.set_encrypted_password(plain_password)
            super().save(update_fields=['password'])
        else:
            super().save(*args, **kwargs)
    
    def get_password(self):
        """Obtener password desencriptada"""
        return self.get_decrypted_password()
```

### Paso 5: Actualizar Vistas

```python
# En deploy/views.py
from security_fixes.sanitization_helpers import InputSanitizer

def deploy_vm(request):
    if form.is_valid():
        try:
            # Sanitizar inputs
            hostname = InputSanitizer.sanitize_hostname(form.cleaned_data['hostname'])
            ip = InputSanitizer.sanitize_ip_address(form.cleaned_data['ip'])
            template = InputSanitizer.sanitize_vm_name(form.cleaned_data['template'])
            
            # Resto del código...
        except ValueError as e:
            messages.error(request, f"Invalid input: {e}")
            return redirect('deploy:deploy_vm')
```

### Paso 6: Remover @csrf_exempt

```python
# En login/views.py
# ANTES:
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def set_language(request):
    ...

# DESPUÉS:
def set_language(request):
    # Usar protección CSRF normal
    ...
```

## 🔍 Verificación

Después de implementar los cambios:

```bash
# Verificar configuración de seguridad
python manage.py check --deploy

# Auditar dependencias
pip install safety
safety check

# Ejecutar tests (si existen)
python manage.py test
```

## ⚠️ Notas Importantes

1. **Backup**: Siempre hacer backup antes de aplicar cambios
   ```bash
   python manage.py dumpdata > backup_$(date +%Y%m%d).json
   cp db.sqlite3 db.sqlite3.backup
   ```

2. **Testing**: Probar en ambiente de desarrollo primero

3. **Credenciales**: Después de encriptar, las credenciales existentes seguirán funcionando

4. **Migración**: La migración de credenciales es irreversible, hacer backup primero

5. **Variables de Entorno**: No commitear el archivo `.env` al repositorio

## 📚 Referencias

- [Django Security Documentation](https://docs.djangoproject.com/en/5.2/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
